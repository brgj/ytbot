import asyncio
import itertools
import threading

import validators
import re

import discord
import yt_dlp
from typing import Optional
from threading import Lock
from functools import reduce, partial
from enum import Enum
from collections.abc import Generator

import util


class State(Enum):
    NOT_STARTED = 1
    RUNNING = 2
    STOPPED = 3


class InvalidStateException(Exception):
    def __init__(self, expected: [State], actual: State):
        super().__init__(f"expected {'one of ' if len(expected) > 1 else ''} {list(map(lambda s: s.name, expected))}, got [{actual}]")


class InvalidInputException(Exception):
    pass


class EmptyQueueException(Exception):
    pass


# The player will disconnect from the voice channel when the queue is exhausted
class YtPlayer(yt_dlp.YoutubeDL):
    __yt_regex = r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(-nocookie)?\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$"

    def __init__(self, logger):
        ytdl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }]
        }
        super().__init__(ytdl_opts)
        self._curr: Optional[tuple[str, dict]] = None
        self._queue: dict[str, dict] = {}
        self._voice_channel = None
        self._state = State.NOT_STARTED
        self._lock = Lock()
        self._logger = logger

    async def get_state(self):
        return self._state

    async def join_channel(self, vc):
        if self._state is not State.NOT_STARTED:
            raise InvalidStateException(expected=[State.NOT_STARTED], actual=self._state)
        await util.async_retry_backoff(3, lambda: self.__try_join_channel(vc))

    async def __try_join_channel(self, vc):
        if len(self._queue) == 0:
            raise EmptyQueueException("unable to join channel when queue is empty!")
        self._voice_channel = vc
        await vc.connect()
        self._state = State.RUNNING
        await self.next()
        return True

    async def get_voice_channel(self):
        if self._state is not State.RUNNING:
            raise InvalidStateException(expected=[State.RUNNING], actual=self._state)
        return self._voice_channel.channel

    async def now_playing(self):
        if self._state is not State.RUNNING:
            raise InvalidStateException(expected=[State.RUNNING], actual=self._state)
        return f"*{self._curr[0]}*"

    async def upcoming(self, count):
        if self._state is State.STOPPED:
            raise InvalidStateException(expected=[State.NOT_STARTED, State.RUNNING], actual=self._state)
        limiter = [None] * (count + 1)
        limiter[count] = "⋯"
        return reduce(lambda s1, s2: f"{s1} ➠ {s2}", map(lambda k, l: f"*{l or k}*", iter(self._queue), limiter))

    async def enqueue(self, query: str = None) -> str:
        return await self.__add_to_playlist(query, lambda s: self._queue.update({s['title']: s}))

    async def push(self, query: str = None) -> str:
        return await self.__add_to_playlist(query,
                                            lambda s: setattr(self, '_queue', {**{s['title']: s}, **self._queue}))

    async def __add_to_playlist(self, query, insert_func) -> str:
        if self._state is State.STOPPED:
            raise InvalidStateException(expected=[State.NOT_STARTED, State.RUNNING], actual=self._state)

        title, songs = self.__extract_songs(query)

        if self._state is State.RUNNING and self._curr is None:
            await self.next()

        return title

    # Invokes the generator to evaluate the song list, and inserts songs into the queue according to the preference
    def __eval_and_insert(self, songs, insert_func):

        # Launch background thread to populate the playlist info
        t = threading.Thread(target=self.__eval_and_insert, kwargs={"songs": songs, "insert_func": insert_func})
        t.start()
        for song in songs:
            with self._lock:
                insert_func(song)

    async def pop(self) -> (str, dict):
        if self._state is State.STOPPED:
            raise InvalidStateException(expected=[State.NOT_STARTED, State.RUNNING], actual=self._state)
        with self._lock:
            k = next(iter(self._queue))
            return k, self._queue.pop(k)

    def remove(self, key) -> (str, dict):
        if self._state is not State.STOPPED:
            raise InvalidStateException(expected=[State.NOT_STARTED, State.RUNNING], actual=self._state)
        with self._lock:
            return key, self._queue.pop(key)

    async def next(self, error=None):
        next_song = None
        if self._state is not State.RUNNING:
            raise InvalidStateException(expected=[State.RUNNING], actual=self._state)

        title, next_song = await util.async_retry_backoff(3, self.pop)

        try:
            # Youtube streaming links expire, so renew the source
            loop = asyncio.get_event_loop()

            to_run = partial(self.extract_info, url=next_song['webpage_url'], download=False)
            self._curr = await loop.run_in_executor(None, to_run)
            self._voice_channel.play(discord.FFmpegPCMAudio(self._curr['url']), after=self.next)
            self._voice_channel.source.volume = 0.5
        except Exception as err:
            self.cleanup()
            raise Exception(f"Failed to play song in YtPlayer: '{type(err)} {{ {str(err)} }}'")

    def __extract_songs(self, query) -> (str, Generator[dict, None, None]):
        # Check that the input is a url or a search term.
        if not validators.url(query):
            # search for the phrase on youtube
            url, similar = self.__search(query)
            self._logger.debug(f"Bot is {similar * 100}% sure that the first result is a match.")
        # Check that the url is a youtube url
        elif re.match(YtPlayer.__yt_regex, query):
            url = query
        else:
            raise InvalidInputException("Please provide a youtube url or a search query for youtube.")

        try:
            metadata = self.extract_info(url, download=False, process=False)

            self._logger.debug(f"Retrieved metadata for '{url}'")
            if "entries" in metadata:
                self._logger.debug("Requested url is for playlist.")
                entries = metadata["entries"]
            else:
                self._logger.debug("Requested url is for single song.")
                entries = map(lambda _: metadata, range(1))

            return metadata["title"], entries
        except Exception as err:
            self._logger.error(
                f"Some catastrophic error occurred while trying to play a song: '{type(err)} {{ {str(err)} }}'")
            self.cleanup()
            raise err

    # TODO implement me
    def __search(self, query) -> (str, float):
        raise NotImplementedError("I haven't implemented search, use a url.")

    def cleanup(self):
        if self._state is not State.RUNNING:
            raise InvalidStateException(expected=[State.RUNNING], actual=self._state)
        self._curr = None
        self._state = State.STOPPED
        try:
            self._voice_channel.disconnect(force=True)
        except Exception:
            pass  # Ignore error on cleanup
        self.__exit__()
