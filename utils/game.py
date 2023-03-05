import pathlib
import discord
from discord.ext import commands
from cogs import game

class AvailableGame(commands.Converter):

    game_dir = pathlib.Path("submodules") 
    ai_dir_name = "ai"
    log_name = "log.txt"
    
    def __init__(self, name, cmd, module) -> None:
        self.name = name
        self.cmd = cmd
        self.module = module
        self.game_dir = AvailableGame.game_dir / self.cmd
        self.ai_dir = self.game_dir / AvailableGame.ai_dir_name
        self.log_file = self.game_dir / AvailableGame.log_name

    @classmethod
    async def convert(cls, ctx: commands.Context, argument: str):
        if argument not in game.Game.games:
            raise commands.BadArgument("Game not found")
        return game.Game.games[argument]


# Discord player i/o function-classes

class Ifunc:

    def __init__(self, channel):
        self.channel: discord.TextChannel = channel

    async def __call__(self, name: str):
        def check(msg: discord.Message):
            return msg.channel == self.channel and msg.author.mention == name
        message: discord.Message = await bot.client.wait_for("message", check=check)
        return message.content

class Ofunc:

    def __init__(self, channel):
        self.channel: discord.TextChannel = channel

    async def __call__(self, output: str):
        await self.channel.send(output)
