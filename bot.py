from typing import Callable, Iterable
import os

import discord
from discord.ext.commands import Bot, Context

from classes.github_client import GH_Client
from classes.openai_client import OPENAI_Client
from classes.token_error import TokenError

client_classes = {"GitHub": GH_Client, "OpenAI": OPENAI_Client}
token_names = {"GitHub": "GH_TOKEN", "OpenAI": "OPENAI_TOKEN"}

class BotObj() :

    def __init__(self) -> None :

        self.client: Bot = Bot(intents=discord.Intents.all(), command_prefix='!')
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

        self.clients: dict[str, GH_Client | OPENAI_Client] = {}
    
    async def connect_client(self, name: str, token: str = None) :
        """
        Connects to the github API
        """

        token_key = token_names[name]

        if token is None :
            token = os.environ[token_key]
        
        try :
            self.clients[name] = client_classes[name](token)
        except TokenError as tkerr :
            await self.channels["debug"].send(f"The {name} token is wrong or has expired, please generate a new one. See README for more info.")
            raise TokenError from tkerr
        except Exception as err :
            await self.channels["debug"].send(err)
            raise Exception from err
        
        os.environ[token_key] = token
            
    def define_on_ready(self, launchers: list[Callable]) -> None :
        @self.client.event
        async def on_ready() :
            self.server = self.client.get_guild(716736874797858957)

            self.channels["notifs"] = self.server.get_channel(1047462537463091212)
            self.channels["debug"] = self.server.get_channel(1048584804301537310)
            self.channels["commands"] = self.server.get_channel(1051626187421650954)
            self.channels["ressources"] = self.server.get_channel(762706892652675122)
            self.channels["games"] = self.server.get_channel(1075844926237061180)
            self.channels["tournament"] = self.server.get_channel(1072461314418548736)

            self.roles["member"] = self.server.get_role(716737589205270559)
            self.roles["admin"] = self.server.get_role(737790034270355488)
            self.roles["bureau"] = self.server.get_role(716737513535963180)
            self.roles["events"] = self.server.get_role(1051629248139505715)

            for launch in launchers :
                launch()

            print("bot ready !")

            await self.channels["debug"].send("Up")
            await self.connect_client("GitHub")
            await self.connect_client("OpenAI")
            
            err, msg = self.clients["GitHub"].reload_repo_tree()
            if err :
                self.channels["debug"].send(msg)
    
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


bot = BotObj()