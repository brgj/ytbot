import discord
import platform
import os
from discord.ext import commands
from discord.ext.commands import Context


class Debug(commands.Cog, name="debug"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="help",
        description="List bot commands"
    )
    async def help(self, context: Context) -> None:
        embed = discord.Embed(
            title="Help", description="List of available commands:", color=0x9C84EF)
        for i in self.bot.cogs:
            cog = self.bot.get_cog(i.lower())
            commands = cog.get_commands()
            data = []
            for command in commands:
                description = command.description.partition('\n')[0]
                data.append(f"/{command.name} - {description}")
            help_text = "\n".join(data)
            embed.add_field(name=i.capitalize(),
                            value=f'```{help_text}```', inline=False)
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="botinfo",
        description="List bot info",
    )
    async def botinfo(self, context: Context) -> None:
        embed = discord.Embed(
            description="Simple bot framework",
            color=0x8D72E3
        )
        embed.set_author(
            name="Bot Information"
        )
        embed.add_field(
            name="Owner:",
            value="Brad",
            inline=True
        )
        embed.add_field(
            name="Python Version:",
            value=f"{platform.python_version()}",
            inline=True
        )
        embed.add_field(
            name="OS:",
            value=f"{platform.system()} {platform.release()} ({os.name})",
            inline=True
        )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="echo",
        description="Echo what the user has input",
    )
    async def echo(self, context: Context, *, input: str) -> None:
        embed = discord.Embed(
            title="**Echo input:**",
            description=f"{context.author}: {input}",
            color=0x8D72E3
        )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="ping",
        description="Check if the bot is alive.",
    )
    async def ping(self, context: Context) -> None:
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"The bot latency is {round(self.bot.latency * 1000)}ms.",
            color=0x9C84EF
        )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="join",
        description="Join the user's voice channel"
    )
    async def join(self, context: Context) -> None:
        channel = context.message.author.voice.channel
        embed = discord.Embed(
            title="**Join channel:**",
            description=f"Joining {channel}",
            color=0x8D72E3
        )
        self.bot.channel = channel
        await channel.connect()
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="leave",
        description="Leave voice chat",
    )
    async def leave(self, context: Context) -> None:
        embed = discord.Embed(
            title="**Leave channel:**",
            description=f"Leaving {self.bot.channel}",
            color=0x8D72E3
        )
        await context.voice_client.disconnect()
        await context.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Debug(bot))
