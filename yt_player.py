import discord
from threading import Lock
from functools import reduce


# The player will disconnect from the voice channel when the queue is exhausted
class YtPlayer:
    def __init__(self, voice_channel):
        self._queue = []
        self._curr = None
        self._voice_channel = voice_channel
        self._player_closed = False
        self._lock = Lock()

    def is_closed(self):
        return self._player_closed

    def get_voice_channel(self):
        return self._voice_channel.channel

    def now_playing(self):
        return f"*{self._curr['title']}*"

    def upcoming(self, count):
        limiter = [None] * (count + 1)
        limiter[count] = "⋯"
        return reduce(lambda s1, s2: f"{s1} ➠ {s2}", map(lambda s, l: f"*{l or s['title']}*", self._queue, limiter))

    def enqueue(self, url):
        with self._lock:
            self._queue.append(url)
        if self._curr is None:
            self.next()

    def push(self, url):
        with self._lock:
            self._queue.insert(0, url)
        if self._curr is None:
            self.next()

    def pop(self):
        with self._lock:
            self._queue.pop()

    def remove(self, url):
        with self._lock:
            self._queue.remove(url)

    def next(self, error=None):
        if self._player_closed:
            raise Exception("Player channel is closed.")
        if self._queue:
            self._curr = self._queue[0]
            self.remove(self._curr)
            try:
                self._voice_channel.play(discord.FFmpegPCMAudio(self._curr["url"]), after=self.next)
                self._voice_channel.source = discord.PCMVolumeTransformer(self._voice_channel.source)
                self._voice_channel.source.volume = 1
            except Exception as err:
                self.cleanup()
                raise Exception(f"Failed to play song in YtPlayer: '{type(err)} {{ {str(err)} }}'")
        else:
            self.cleanup()

    def cleanup(self):
        self._curr = None
        self._player_closed = True
        try:
            self._voice_channel.disconnect(force=True)
        except Exception:
            pass  # Ignore error on cleanup

