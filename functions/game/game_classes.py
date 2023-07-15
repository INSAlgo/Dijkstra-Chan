import pathlib
import discord
import importlib
from discord.ext import commands
from cogs import game


class AvailableGame(commands.Converter):

    games = dict()

    games_path = pathlib.Path("games") 
    AI_DIR_NAME = "ai"
    LOG_FIlE_NAME = "log.txt"
    
    def __init__(self, games_path) -> None:
        self.package = importlib.import_module(f"{games_path.parent}.{games_path.name}")
        self.module = self.package.game
        self.name = self.package.NAME
        self.cmd = self.package.COMMAND
        self.url = self.package.URL
        self.games_path = games_path
        self.ai_path = self.games_path / AvailableGame.AI_DIR_NAME
        self.log_file = self.games_path / AvailableGame.LOG_FIlE_NAME

    @classmethod
    def load_games(cls):
        if cls.games_path.is_dir():
            for game_path in cls.games_path.iterdir():
                if game_path.name not in cls.games:
                    cls.games[game_path.name] = AvailableGame(game_path)

    @classmethod
    async def convert(cls, ctx: commands.Context, argument: str):
        if argument not in cls.games:
            raise commands.BadArgument("Game not found, see `game list`")
        return cls.games[argument]


# Discord player i/o function-classes

class Ifunc:

    def __init__(self, channel, bot):
        self.bot = bot
        self.channel: discord.TextChannel = channel

    async def __call__(self, name: str):
        def check(msg: discord.Message):
            return msg.channel == self.channel and msg.author.mention == name
        message: discord.Message = await self.bot.wait_for("message", check=check)
        return message.content

class Ofunc:

    def __init__(self, channel):
        self.channel: discord.TextChannel = channel

    async def __call__(self, output: str):
        await self.channel.send(output)
