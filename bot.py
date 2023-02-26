from typing import Callable, Iterable
import os

import discord
from discord.ext.commands import Bot, Context

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

            self.channels["notifs"] = self.server.get_channel(1047462537463091212)
            self.channels["debug"] = self.server.get_channel(1048584804301537310)
            self.channels["commands"] = self.server.get_channel(1051626187421650954)
            self.channels["ressources"] = self.server.get_channel(762706892652675122)

            self.roles["member"] = self.server.get_role(716737589205270559)
            self.roles["admin"] = self.server.get_role(737790034270355488)
            self.roles["bureau"] = self.server.get_role(716737513535963180)
            self.roles["events"] = self.server.get_role(1051629248139505715)

            for launch in launchers :
                launch()

            print("bot ready !")
            await self.channels["debug"].send("Up")
    
    def run(self) :
        self.client.run(self.token)
    
    def check_perm(self, ctx: Context, channels: Iterable[str] = set(), roles: Iterable[str] = set()) :
        """
        Returns `True` if the ctx is in one of the given channels (or debug),
        and the author has one of the given roles,
        else returns `False`.

        If `roles` is omitted, any role is valid.
        If `channels` is omitted, only debug channel is valid
        """
        
        channels = set(channels)
        channels.add("debug")
        for ch_name in channels :
            if ctx.channel == self.channels[ch_name] :
                break
        else :
            return False
        
        if not roles :
            return True
        
        for r_name in roles :
            if self.roles[r_name] in ctx.author.roles :
                break
        else :
            return False
        return True


bot = SingleBot()