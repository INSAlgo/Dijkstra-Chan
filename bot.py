from typing import Callable
import os

import discord
from discord.ext.commands import Bot

class SingletonMeta(type) :

    _instances = {}

    def __call__(cls, *args, **kwargs) :
        if cls not in cls._instances :
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

class SingleBot(metaclass=SingletonMeta) :

    def __init__(self) -> None :

        self.client = Bot(intents=discord.Intents.all(), command_prefix='!')
        self.client.remove_command('help')

        try :
            self.token = os.environ["TOKEN"]
        except KeyError as e:
            print("Missing discord bot token as 'TOKEN' in environment variables.")
            print("Ask an administrator of the bot to obtain it.")
            raise KeyError(e)

        self.server: discord.Guild

        self.channels: dict[str, discord.TextChannel] = {}
        self.roles: dict[str, discord.Role] = {}

    def define_on_ready(self, launchers: list[Callable]) -> None :
        @self.client.event
        async def on_ready() :
            self.server = self.client.get_guild(716736874797858957)

            self.channels["notif"] = self.server.get_channel(1047462537463091212)
            self.channels["debug"] = self.server.get_channel(1048584804301537310)
            self.channels["command"] = self.server.get_channel(1051626187421650954)
            self.channels["ressources"] = self.server.get_channel(762706892652675122)

            self.roles["member"] = self.server.get_role(716737589205270559)
            self.roles["admin"] = self.server.get_role(737790034270355488)
            self.roles["bureau"] = self.server.get_role(716737513535963180)
            self.roles["event"] = self.server.get_role(1051629248139505715)

            for launch in launchers :
                launch()

            print("bot ready !")
            await self.channels["debug"].send("Up")
    
    def run(self) :
        self.client.run(self.token)

bot = SingleBot()