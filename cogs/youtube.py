import asyncio
import discord
import random
import sys
import traceback
from discord.ext import commands
from discord.ext.commands import Context

import bot
from yt_dl_source import YTDLSource
from yt_player import YtPlayer, State


class VoiceConnectionError(commands.CommandError):
    """Custom Exception class for connection errors."""


class InvalidVoiceChannel(VoiceConnectionError):
    """Exception for cases of invalid Voice Channels."""


class Youtube(commands.Cog, name="youtube"):
    def __init__(self, bot):
        self.bot = bot
        self.players = {}
        if sys.platform == "darwin":
            discord.opus.load_opus('lib/darwin/libopus.0.dylib')

    async def cleanup(self, guild):
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass

        try:
            del self.players[guild.id]
        except KeyError:
            pass

    async def __local_check(self, ctx):
        """A local check which applies to all commands in this cog."""
        if not ctx.guild:
            raise commands.NoPrivateMessage
        return True

    async def __error(self, ctx, error):
        """A local error handler for all errors arising from commands in this cog."""
        if isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.send('This command can not be used in Private Messages.')
            except discord.HTTPException:
                pass
        elif isinstance(error, InvalidVoiceChannel):
            await ctx.send('Error connecting to Voice Channel. '
                           'Please make sure you are in a valid channel or provide me with one')

        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    def get_player(self, ctx):
        """Retrieve the guild player, or generate one."""
        try:
            player = self.players[ctx.guild.id]
        except KeyError:
            player = YtPlayer(ctx, bot.logger)
            self.players[ctx.guild.id] = player

        return player

    @commands.command(name='join', aliases=['connect', 'j'], description="connects to voice")
    async def connect_(self, ctx, *, channel: discord.VoiceChannel=None):
        """Connect to voice.
        Parameters
        ------------
        channel: discord.VoiceChannel [Optional]
            The channel to connect to. If a channel is not specified, an attempt to join the voice channel you are in
            will be made.
        This command also handles moving the bot to different channels.
        """
        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                embed = discord.Embed(title="", description="No channel to join. Please call `,join` from a voice channel.", color=discord.Color.green())
                await ctx.send(embed=embed)
                raise InvalidVoiceChannel('No channel to join. Please either specify a valid channel or join one.')

        vc = ctx.voice_client

        if vc:
            if vc.channel.id == channel.id:
                return
            try:
                await vc.move_to(channel)
            except asyncio.TimeoutError:
                raise VoiceConnectionError(f'Moving to channel: <{channel}> timed out.')
        else:
            try:
                await channel.connect()
            except asyncio.TimeoutError:
                raise VoiceConnectionError(f'Connecting to channel: <{channel}> timed out.')
        await ctx.send(f'**Joined `{channel}`**')

    @commands.hybrid_command(
        name="play",
        aliases=['sing', 'p'],
        description="Join the user's voice channel and play url"
    )
    async def play(self, ctx: Context, *, q: str) -> None:
        async with ctx.typing():
            # TODO: Removeme; Default for testing
            if q == "q":
                q = "https://www.youtube.com/watch?v=4BgF7Y3q-as"

            vc = ctx.voice_client

            if not vc:
                await ctx.invoke(self.connect_)

            self.bot.logger.debug(f"Bot gathering metadata for '{q}'")
            player = self.get_player(ctx)
            # TODO: should probably download and chunk in order to avoid http read errors messing up the stream.
            # If download is False, source will be a dict which will be used later to regather the stream.
            # If download is True, source will be a discord.FFmpegPCMAudio with a VolumeTransformer.
            source = await YTDLSource.create_source(ctx, q, loop=self.bot.loop, download=False)

            await player.queue.put(source)

        embed = discord.Embed(
            title="**Playing music**",
            color=0x8D72E3
        )
        embed.add_field(name=f"__Now Playing__ (#{self.bot.yt_player.get_voice_channel()})",
                        value=self.bot.yt_player.now_playing(), inline=False)
        embed.add_field(name="__Changes to Playlist__", value=new_song, inline=False)
        embed.add_field(name="__More Info__", value="Type `/playlist` for queued music.", inline=False)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Youtube(bot))
