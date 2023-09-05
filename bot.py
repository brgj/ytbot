import asyncio
import yaml
import logging
import os
import platform
import random
import sys
import discord
import glob
import hashlib
from discord.ext import commands, tasks
from discord.ext.commands import Bot, Context

if not os.path.isfile(f"{os.path.realpath(os.path.dirname(__file__))}/config.yaml"):
    sys.exit("'config.yaml' not found!")
else:
    with open(f"{os.path.realpath(os.path.dirname(__file__))}/config.yaml") as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

# We only need messages and voice_states for this bot right now.
# intents = discord.Intents(messages=True, voice_states=True, guilds=True, integrations=True)
intents = discord.Intents.default()

# Create logger and add handler
logger = logging.getLogger("ytbot")
logger.setLevel(config.get("log_level") or logging.DEBUG)
# logger.addHandler(logging.StreamHandler())
fh = logging.FileHandler(config.get("logfile") or 'ytbot.log')
fmt = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
fh.setFormatter(fmt)
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)

# Create bot and add logger/config
bot = Bot(command_prefix=commands.when_mentioned, intents=intents, help_command=None, case_insensitive=True)
bot.logger = logger
bot.config = config
bot.yt_player = None


def get_proj_hash() -> str:
    filenames = glob.glob("**[!venv]/*.py", recursive=True)
    filenames += glob.glob("*.py")
    filenames += glob.glob("*.yaml")
    md5 = hashlib.md5()

    for filename in filenames:
        with open(filename, 'rb') as inputfile:
            data = inputfile.read()
            md5.update(data)

    return md5.hexdigest()


"""
Executes when the bot is ready
"""
@bot.event
async def on_ready() -> None:
    bot.logger.debug("-------------------")
    bot.logger.debug(f"project hash: {get_proj_hash()}")
    bot.logger.debug("-------------------")
    bot.logger.info(f"Logged in as {bot.user.name}")
    bot.logger.info(f"discord.py API version: {discord.__version__}")
    bot.logger.info(f"Python version: {platform.python_version()}")
    bot.logger.info(f"Running on: {platform.system()} {platform.release()} ({os.name})")
    bot.logger.info("-------------------")
    status_task.start()
    await bot.tree.sync()


@tasks.loop(minutes=0.5)
async def status_task() -> None:
    statuses = ["Fartin' in a bar (a place where alcoholic drinks are served, or a long, straight piece of material)",
                "Fartin' in a car (a motor vehicle designed for transportation on roads)",
                "Fartin' quite bizarre (very strange or unusual)",
                "Fartin' near a carr (a type of wetland or bog, or a vehicle for carrying goods over rough terrain)"
                "Fartin' on a char (to burn or blacken the surface of something, or a fish of the trout family)",
                "Fartin' with a dar (a silver coin formerly used in Persia and the Middle East, or short for \"darling\")",
                "Fartin' from afar (at or to a considerable distance, or distant in space or time)",
                "Fartin' on a gar (a type of fish found in fresh and brackish waters of North and Central America)",
                "Fartin' at a gnar (a knotty, twisted protuberance on a tree trunk or root)",
                "Fartin' in a jar (a wide-mouthed container made of glass, pottery, or metal)",
                "Fartin' on a mar (a lake, sea, or ocean that is partially enclosed by land)",
                "Fartin' on par (a standard level of performance or achievement, or the number of strokes a good golfer should take to complete a hole)",
                "Fartin' near a scar (a mark left on the skin or other tissue after a wound has healed, or a steep, jagged rock or cliff)",
                "Fartin' on a spar (a stout pole or beam, or a mineral that is a common component of rocks)",
                "Fartin' with a tar (a thick, sticky black liquid made by heating wood, coal, or other organic matter in the absence of air, or a sailor)",
                "Fartin' on a tahr (a type of wild goat found in the Himalayas)",
                "Fartin' on a thar (an old spelling of \"tahr,\" a type of wild goat found in the mountains of central Asia)",
                "Fartin' on a barre (a horizontal bar used in ballet for support or exercise)",
                "Fartin' with a czar (an emperor or king in Russia or other Slavic countries)",
                "Fartin' in a jarre (a large earthenware or glass container used for storage or fermentation)",
                "Fartin' on a sare (a traditional garment worn by women in India and other South Asian countries)",
                "Fartin' on a scarre (an old spelling of \"scare,\" meaning to cause fear or alarm)",
                "Fartin' with a sparre (an old spelling of \"spar,\" meaning a stout pole or beam)",
                "Fartin' on a starre (a distant luminous object in the sky, typically a large, self-luminous celestial body)",
                "Fartin' at a tharre (an old spelling of \"thar,\" meaning a wild goat found in the mountains of central Asia)",
                "Fartin' on a tsar (an alternative spelling of \"czar,\" meaning an emperor or king in Russia or other Slavic countries)",
                "Fartin' on a tzar (an alternative spelling of \"czar,\" meaning an emperor or king in Russia or other Slavic countries)",
                "Fartin' with a var (an old spelling of \"war,\" meaning a state of armed conflict between nations, states, or groups)",
                "Fartin' on a charre (a type of flat iron used in tailoring)",
                "Fartin' at a star (a distant luminous object in the sky, typically a large, self-luminous celestial body)",
                "Fartin' on a har (a medieval stringed instrument similar to a lyre)",
                "Fartin' with a sparre (a spear or javelin used in medieval times)",
                "Fartin' for a vahrr (a hypothetical unit of measurement in science fiction or fantasy)",
                "Fartin' on a lahar (a type of volcanic mudflow)",
                "Fartin' as a scarre (a medieval battle cry or war horn signal)",
                "Fartin' on a zar (a monetary unit in some countries, such as Albania and Iran)",
                "Fartin' on a jarre (a French musician known for his electronic music)",
                "Fartin' on a yar (an informal term for a pirate ship)",
                "Fartin' for a khar (a unit of measurement for the weight of precious stones)",
                "Fartin' on a snar (a tangled or knotted mass of hair or thread)",
                "Fartin' on a jhar (a type of tree found in India and Southeast Asia)",
                "Fartin' as a blar (to cry or wail loudly and mournfully)",
                "Fartin' on an iar (short for \"integrated advanced robot\")",
                "Fartin' on a larre (a type of South American iguana)",
                "Fartin' on some parh (a type of coarse grass found in India and Pakistan)",
                "Fartin' on a guitar (a musical instrument with strings that is typically played by strumming or plucking)",
                "Fartin' on a memoir (an autobiographical account of someone's life, often focusing on specific experiences or events)",
                "Fartin' while ajar (partially open or not completely closed)",
                "Fartin' in a cigar (a type of rolled tobacco leaf that is typically smoked)",
                "Fartin' on lumbar (relating to or situated in the lower back or loin area)",
                "Fartin' on radar (a system that uses radio waves to detect the presence and location of objects)",
                "Fartin' in a seminar (a meeting or conference for discussion or instruction on a specific topic)",
                "Fartin' on Avatar (a 2009 science fiction film directed by James Cameron, set in the mid-22nd century on the habitable moon Pandora, where humans mine a valuable mineral and encounter the indigenous Na'vi population)",
                "Fartin' in a reservoir (a large natural or artificial lake used for the storage of water)",
                "Fartin' in a samovar (a metal urn used to boil water for tea, typically used in Russia and other parts of Eastern Europe and Asia)",
                "Fartin' on a handlebar (the steering mechanism of a bicycle or motorcycle, typically consisting of a curved bar with handgrips at each end)",
                "Fartin' on cinnabar (a bright red mineral that is the chief source of mercury)",
                "Fartin' on a motorcar (an archaic term for a motor vehicle, typically used in the early 20th century)",
                "Fartin' a repertoire (a stock of plays, dances, songs, or other works that a performer is prepared to present)",
                "Fartin' on saphar (a unit of measurement used in ancient India and Persia, equivalent to about 1.8 miles)",
                "Fartin' on kafar (a Hebrew word meaning \"village\" or \"hamlet\")",
                "Fartin' a catarrh (an excessive discharge of mucus, typically from the nose or throat)",
                "Fartin' on a dvar (a Hebrew word meaning \"word\" or \"thing\")",
                "Fartin' on an ulnar (relating to the ulna, a bone in the forearm)",
                "Fartin' on a canthar (a type of beetle, typically with metallic green or blue coloring)",
                "Fartin' arr (a Scottish word meaning \"every\")",
                "Fartin' on a plenipotentiary (a person who has full power to take action on behalf of their government, typically in a foreign country)",
                "Fartin' on your yar (a Persian and Turkish word meaning \"friend\" or \"companion\")",
                "Fartin' on bursar (a person responsible for financial matters at a college or university)",
                "Fartin' on chukar (a type of game bird found in Eurasia and North America)",
                "Fartin' on zaffar (a Persian word for saffron, a spice derived from the crocus flower)",
                "Fartin' on caviar (salt-cured fish eggs, typically from sturgeon and considered a delicacy)",
                "Fartin' on rhabarbar (a German word for rhubarb, a sour-tasting plant often used in desserts)",
                "Fartin' on alcazar (a Spanish word for a fortress or castle)",
                "Fartin' on a crowbar (a metal tool with a flattened end, used for prying or breaking things)",
                "Fartin' on kibar (an Arabic word meaning \"noble\" or \"dignified\")",
                "Fartin' on a vicar (a priest or minister, especially one who serves as a representative of a higher-ranking member of the clergy)",
                "Fartin' on papar (a type of fabric often used for dresses and blouses)",
                "Fartin' on a minibar (a small refrigerator in a hotel room or other space)",
                "Fartin' on a superstar (a very famous or successful performer or athlete)",
                "Fartin' in a bazaar (a marketplace or shopping district, especially in Middle Eastern and North African countries)",
                "Fartin' on a handcar (a small railroad car powered by hand)",
                "Fartin' in a handle jar (a container with a handle for holding liquids or other substances)",
                "Fartin' like velar (a sound made by obstructing the airflow in the mouth with the tongue or soft palate)"
                ]
    await bot.change_presence(activity=discord.Game(random.choice(statuses)))

"""
Executes every time a message is sent
"""
@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author == bot.user or message.author.bot:
        return
    await bot.process_commands(message)

"""
Executes every time a normal command has been executed
"""
@bot.event
async def on_command_completion(context: Context) -> None:
    full_command_name = context.command.qualified_name
    split = full_command_name.split(" ")
    executed_command = str(split[0])
    bot.logger.info(f"Executed {executed_command} command")

"""
Executes every time a command throws an error
"""
@bot.event
async def on_command_error(context: Context, error) -> None:
    if isinstance(error, commands.CommandOnCooldown):
        minutes, seconds = divmod(error.retry_after, 60)
        embed = discord.Embed(
            description=f"Command on cooldown ({f'{round(minutes)} minutes'}, {f'{round(seconds)} seconds'})",
            color=0xFF0000
        )
        await context.send(embed=embed)
    elif isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            description="User is missing permission(s) `" + ", ".join(
                error.missing_permissions) + "` to perform this command",
            color=0xFF0000
        )
        await context.send(embed=embed)
    elif isinstance(error, commands.BotMissingPermissions):
        embed = discord.Embed(
            description="Bot is missing the permission(s) `" + ", ".join(
                error.missing_permissions) + "` to perform this command",
            color=0xFF0000
        )
        await context.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            description=str(error),
            color=0xFF0000
        )
        await context.send(embed=embed)
    else:
        raise error


async def load_cogs() -> None:
    logger.info(f"loading cogs from '{os.path.realpath(os.path.dirname(__file__))}/cogs'...")
    logger.info(f"content: {os.listdir(f'{os.path.realpath(os.path.dirname(__file__))}/cogs')}")
    for file in os.listdir(f"{os.path.realpath(os.path.dirname(__file__))}/cogs"):
        if file.endswith(".py"):
            extension = file[:-3]
            try:
                await bot.load_extension(f"cogs.{extension}")
                bot.logger.info(f"Loaded extension '{extension}'")
            except Exception as e:
                exception = f"{type(e).__name__}: {e}"
                bot.logger.error(
                    f"Failed to load extension {extension}\n{exception}")


asyncio.run(load_cogs())
bot.run(config["token"])
