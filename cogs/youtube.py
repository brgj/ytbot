import discord
import yt_dlp
from discord.ext import commands
from discord.ext.commands import Context


class Youtube(commands.Cog, name="youtube"):
    def __init__(self, bot):
        self.bot = bot
        # TODO: Make this work on non-darwin systems
        discord.opus.load_opus('lib/darwin/libopus.0.dylib')

    @commands.hybrid_command(
        name="play",
        description="Join the user's voice channel and play url"
    )
    async def play(self, context: Context, *, url: str) -> None:
        channel = context.message.author.voice.channel
        embed = discord.Embed(
            title="**Playing music:**",
            description=f"Joining {channel} and playing {url}",
            color=0x8D72E3
        )

        if channel:
            vc = await channel.connect()
            self.bot.channel = channel
            ydl_opts = {
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192"
                }],
                "outtmpl": "song"
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            vc.play(discord.FFmpegPCMAudio("song.mp3"))
            vc.source = discord.PCMVolumeTransformer(vc.source)
            vc.source.volume = 0.1
            await context.send(embed=embed)
        else:
            await context.send("You are not connected to a voice channel.")


async def setup(bot):
    await bot.add_cog(Youtube(bot))
