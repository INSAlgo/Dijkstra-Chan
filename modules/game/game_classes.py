from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
from types import ModuleType
from importlib import import_module

import discord
import discord.ext.commands as cmds

from main import CustomBot


class AvailableGame(cmds.Converter):

    games: list[AvailableGame] = []

    games_path = Path("games") 
    AI_DIR_NAME = "ai"
    LOG_FIlE_NAME = "log.txt"
    
    def __init__(self, game_path: Path) -> None:
        # No way to properly type self.package...
        # It would be cool to type self.module.main as a proper async function.
        self.package = import_module(f"{game_path.parent}.{game_path.name}")
        self.module: ModuleType = self.package.game
        self.name: str = self.package.NAME
        self.cmd: str = self.package.COMMAND
        self.url: str = self.package.URL
        self.game_path = game_path
        self.ai_path = self.game_path / AvailableGame.AI_DIR_NAME
        self.log_file = self.game_path / AvailableGame.LOG_FIlE_NAME

    @classmethod
    def load_games(cls):
        if cls.games_path.is_dir():
            loaded_path_names = set(game.game_path.name for game in cls.games)
            for game_path in cls.games_path.iterdir():
                if game_path.name not in loaded_path_names:
                    cls.games.append(AvailableGame(game_path))

    @classmethod
    async def convert(cls, ctx: cmds.Context, argument: str):
        for game in cls.games:
            if game.cmd == argument:
                return game
        raise cmds.BadArgument("Game not found, see `game list`")


# Discord player i/o function-classes

class Ifunc:

    def __init__(self, channel: discord.TextChannel, bot: CustomBot):
        self.bot = bot
        self.channel = channel

    async def __call__(self, name: str):
        def check(msg: discord.Message):
            return msg.channel == self.channel and msg.author.mention == name
        message: discord.Message = await self.bot.wait_for("message", check=check)
        return message.content

class Ofunc:

    def __init__(self, channel: discord.TextChannel):
        self.channel = channel

    async def __call__(self, *args, **kwargs):
        await self.channel.send(*args, **kwargs)
