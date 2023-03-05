import discord
from discord.ext import commands
from discord.ext.commands import Command, Cog, Group
from typing import Mapping, Optional, List, Any
import logging
logger = logging.getLogger(__name__)

class CustomHelp(commands.HelpCommand):

    async def send_bot_help(self, mapping: Mapping[Optional[Cog], List[Command[Any, ..., Any]]], /) -> None:

        desc = []
        desc.append(f"INSAlgo's personal bot, available on [GitHub](https://github.com/INSAlgo/Dijkstra-Chan) and open to contributions.")
        desc.append(f"The following is a list of the commands, that you can use with the prefix `{self.context.prefix}`")
        desc.append(f"Get more help for an individual command with `{self.context.prefix}help <command>`.")
        embed = discord.Embed(color=discord.Color.dark_grey(),
                              title = "👋 Dijkstra-Chan's help",
                              description="\n".join(desc))
        
        for cog, cmds in mapping.items():
            cmds = (cmd for cmd in cmds if not cmd.hidden and not self.show_hidden)
            category = ""
            desc = []
            if cog:
                category = f"{cog.qualified_name}"
                desc.append(f"{cog.description}")
            else:
                category = "Other"
            visible_cmds = False
            for cmd in cmds:
                desc.append(f"`{cmd.qualified_name}`")
                desc.append(f"{cmd.short_doc}")
                visible_cmds = True
            if visible_cmds:
                embed.add_field(name=category,
                                value = "\n".join(desc),
                                inline=False)

        await self.context.send(embed=embed)

    async def send_command_help(self, command: Command[Any, ..., Any], /) -> None:

        desc = []
        params = (f"<{param}>" for param in command.clean_params.keys())
        desc.append(f"`{self.context.prefix}{command.qualified_name} {' '.join(params)}`")

        embed = discord.Embed(color=discord.Color.dark_grey(),
                              title = "Command help",
                              description="\n".join(desc))

        if command.help:
            embed.add_field(name="Description",
                            value=f"{command.help}")

        await self.context.send(embed=embed)

    async def send_group_help(self, group: Group[Any, ..., Any], /) -> None:

        desc = []
        desc.append(group.help)
        desc.append(f"Get more help for an individual command with `{self.context.prefix}help <command>`")

        embed = discord.Embed(color=discord.Color.dark_grey(),
                              title = "Group command help",
                              description="\n".join(desc))
        
        for cmd in group.commands:
            if cmd.hidden and not self.show_hidden:
                continue
            desc = []
            desc.append(f"`{cmd.qualified_name}`")
            desc.append(f"{cmd.short_doc}\n")
            embed.add_field(name=cmd.name.capitalize(),
                            value="\n".join(desc),
                            inline=False)

        # embed.add_field(name="Commands",
        #                 value = "\n".join(desc),
        #                 inline=False)

        await self.context.send(embed=embed)
