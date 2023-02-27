import discord
import yt_dlp
import threading
from discord.ext import commands
from discord.ext.commands import Context
from sys import platform
from yt_player import YtPlayer


class Youtube(commands.Cog, name="youtube"):
    def __init__(self, bot):
        self.bot = bot
        if platform == "darwin":
            discord.opus.load_opus('lib/darwin/libopus.0.dylib')


    @commands.hybrid_command(
        name="playlist",
        description="List upcoming songs in the playlist"
    )
    async def playlist(self, context: Context) -> None:
        if self.bot.yt_player is None or self.bot.yt_player.is_closed:
            await context.send("There is no player active in a voice channel.")

        embed = discord.Embed(
            title="**Playlist**",
            color=0x8D72E3
        )
        embed.add_field(name=f"__Now Playing__ (#{self.bot.yt_player.get_voice_channel()})",
                        value=self.bot.yt_player.now_playing(), inline=False)
        embed.add_field(name="__Upcoming__", value=self.bot.yt_player.upcoming(5), inline=False)
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="play",
        description="Join the user's voice channel and play url"
    )
    async def play(self, context: Context, *, url: str) -> None:
        if self.bot.yt_player is None or self.bot.yt_player.is_closed:
            channel = context.message.author.voice.channel
            if not channel:
                await context.send("You are not connected to a voice channel.")
                return
            self.bot.logger.debug(f"Bot connecting to channel {channel}")
            vc = await channel.connect()
            self.bot.yt_player = YtPlayer(vc)

        self.bot.logger.debug(f"Bot gathering metadata for '{url}'")
        ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }]
        }
        ydl = None
        try:
            ydl = yt_dlp.YoutubeDL(ydl_opts)
            metadata = ydl.extract_info(url, download=False, process=False)
            entries = None
            self.bot.logger.debug(f"Retrieved metadata for '{url}'")
            if "entries" in metadata:
                self.bot.logger.debug("Requested url is for playlist."
                                      " Resolving first song and processing playlist.")
                entries = metadata["entries"]
                first_entry = next(entries)
                if "url" not in first_entry:
                    raise Exception(f"url property not found in song info: '{first_entry}'")

                self.bot.logger.debug(f"Resolving first song url: '{first_entry['url']}'")
                song_info = ydl.extract_info(first_entry['url'], download=False)

                changes = f"Added song '{song_info['title']}' plus others from youtube playlist '{metadata['title']}'"
            else:
                self.bot.logger.debug(f"Requested url is not for playlist. Resolving song.")
                song_info = ydl.extract_info(url, download=False)
                changes = f"Added song '{song_info['title']}'"

            if "url" not in song_info:
                raise Exception(f"url property not found in song info: '{song_info}'")

            self.bot.yt_player.enqueue(song_info)

            if entries:
                # Launch background thread to populate the playlist info
                t = threading.Thread(target=self.add_to_playlist, kwargs={"entries": entries, "ydl": ydl})
                t.start()
            else:
                ydl.__exit__()
        except Exception as err:
            self.bot.logger.error(f"Failed to play song: '{type(err)} {{ {str(err)} }}'")
            self.bot.yt_player.cleanup()
            if ydl:
                ydl.__exit__()
            raise err
        embed = discord.Embed(
            title="**Playing music**",
            color=0x8D72E3
        )
        embed.add_field(name=f"__Now Playing__ (#{self.bot.yt_player.get_voice_channel()})",
                        value=self.bot.yt_player.now_playing(), inline=False)
        embed.add_field(name="__Changes to Playlist__", value=changes, inline=False)
        embed.add_field(name="__More Info__", value="Type `/playlist` for queued music.", inline=False)
        await context.send(embed=embed)

    def add_to_playlist(self, entries, ydl):
        with ydl:
            for entry in entries:
                song_info = ydl.extract_info(entry['url'], download=False)
                self.bot.yt_player.enqueue(song_info)


async def setup(bot):
    await bot.add_cog(Youtube(bot))
