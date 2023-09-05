import discord
from discord.ext import commands
from discord.ext.commands import Context
from sys import platform
from yt_player import YtPlayer, State


class Youtube(commands.Cog, name="youtube"):
    def __init__(self, bot):
        self.bot = bot
        self.yt_player = YtPlayer(bot.logger)
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
    async def play(self, context: Context, *, q: str) -> None:
        # TODO: Removeme; Default for testing
        if q == "q":
            q = "https://www.youtube.com/watch?v=4BgF7Y3q-as"

        self.bot.logger.debug(f"Bot gathering metadata for '{q}'")

        try:
            new_song = await self.yt_player.enqueue(q)
        except Exception as err:
            self.bot.logger.error(f"Failed to play song: '{type(err)} {{ {str(err)} }}'")
            raise err

        if await self.yt_player.get_state() is not State.RUNNING:
            channel = context.message.author.voice.channel
            if not channel:
                await context.send("You are not connected to a voice channel.")
                return
            self.bot.logger.debug(f"Bot connecting to channel {channel}")
            await self.yt_player.join_channel(channel)

        embed = discord.Embed(
            title="**Playing music**",
            color=0x8D72E3
        )
        embed.add_field(name=f"__Now Playing__ (#{self.bot.yt_player.get_voice_channel()})",
                        value=self.bot.yt_player.now_playing(), inline=False)
        embed.add_field(name="__Changes to Playlist__", value=new_song, inline=False)
        embed.add_field(name="__More Info__", value="Type `/playlist` for queued music.", inline=False)
        await context.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Youtube(bot))
