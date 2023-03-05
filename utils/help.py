import discord
from discord.ext import commands
from discord.ext.commands import Command, Cog
from typing import Mapping, Optional, List, Any
import logging
logger = logging.getLogger(__name__)

class CustomHelp(commands.HelpCommand):

    async def send_bot_help(self, mapping: Mapping[Optional[Cog], List[Command[Any, ..., Any]]], /) -> None:

        desc = f"INSAlgo's personal bot, available on [GitHub](https://github.com/INSAlgo/Dijkstra-Chan) and open to contributions.\n"
        desc += f"The following is a list of the commands, that you can use with the prefix `{self.context.prefix}`\n"
        desc += f"Get more help for an individual command with `{self.context.prefix}help <command>`."
        embed = discord.Embed(color=discord.Color.dark_grey(),
                              title = "Dijkstra-Chan's help",
                              description=desc)
        
        for cog, cmds in mapping.items():
            if not cmds:
                continue
            category = ""
            desc = []
            if cog:
                category = f"{cog.qualified_name}"
                desc.append(f"{cog.description}\n")
            for cmd in cmds:
                desc.append(f"`{cmd.qualified_name}`")
                desc.append(f"{cmd.short_doc}\n")
            embed.add_field(name=category,
                            value = "\n".join(desc),
                            inline=False)


        await self.context.send(embed = embed)
