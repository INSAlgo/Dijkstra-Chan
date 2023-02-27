import pathlib

import discord


# Constants :

GAMES_DIR = pathlib.Path("submodules")
AI_DIR_NAME = "ai"


# Game object :

class Game():
    
    def __init__(self, name, directory, cmd, module) -> None:
        self.name = name
        self.directory = directory
        self.cmd = cmd
        self.module = module
        self.game_dir = GAMES_DIR / self.directory
        self.ai_dir = self.game_dir / AI_DIR_NAME
        self.log_file = self.game_dir / "log.txt"

GAMES = {"p4": Game("Connect 4", "puissance4", "p4", puissance4, )}


# discord player i/o function-classes :

class Ifunc:

    def __init__(self, channel):
        self.channel = channel

    async def __call__(self, name: str):
        def check(msg):
            return msg.channel == self.channel and msg.author.mention == name
        message: discord.Message = await bot.client.wait_for("message", check=check)
        return message.content

class Ofunc:

    def __init__(self, channel):
        self.channel = channel

    async def __call__(self, output: str):
        await self.channel.send(output)