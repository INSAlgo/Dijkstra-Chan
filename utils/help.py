import discord
from discord.ext import commands
from discord.ext.commands import Command, Cog, Group
from typing import Mapping, Optional, List, Any
import logging
logger = logging.getLogger(__name__)

class CustomHelp(commands.HelpCommand):

    def __add_help_field(self, embed: discord.Embed):
        embed.add_field(name="Help",
                        value=f"Get more help for an individual command with `help <command>`",
                        inline=False)

    async def send_bot_help(self, mapping: Mapping[Optional[Cog], List[Command[Any, ..., Any]]], /) -> None:

        desc = []
        desc.append(f"INSAlgo's personal bot ! Available on [GitHub](https://github.com/INSAlgo/Dijkstra-Chan) and open to contributions.")
        desc.append(f"The following is a list of the commands that you can use with the prefix `{self.context.prefix}`")
        embed = discord.Embed(color=discord.Color.dark_grey(),
                              title = "Dijkstra-Chan's help",
                              description="\n".join(desc))

        for cog, cmds in mapping.items():
            if cog:
                category = f"{cog.qualified_name}"
            else:
                category = "Other"
            visible_cmds = False
            desc = []
            for cmd in cmds:
                if cmd.hidden and not self.show_hidden:
                    continue
                desc.append(f"`{cmd.qualified_name}`")
                desc.append(f"{cmd.short_doc}")
                visible_cmds = True
            if visible_cmds:
                embed.add_field(name=category,
                                value = "\n".join(desc),
                                inline=False)

        self.__add_help_field(embed)
        await self.context.send(embed=embed)


    async def send_cog_help(self, cog: Cog, /) -> None:

        embed = discord.Embed(color=discord.Color.dark_grey(),
                              title="Category help",
                              description=cog.description)
        
        for cmd in cog.get_commands():
            if cmd.hidden and not self.show_hidden:
                continue
            desc = []
            desc.append(f"`{cmd.qualified_name}`")
            desc.append(f"{cmd.short_doc}\n")
            embed.add_field(name=cmd.name.capitalize(),
                            value="\n".join(desc),
                            inline=False)

        self.__add_help_field(embed)
        await self.context.send(embed=embed)


    async def send_group_help(self, group: Group[Any, ..., Any], /) -> None:

        embed = discord.Embed(color=discord.Color.dark_grey(),
                              title = "Group command help",
                              description=group.help)
        
        for cmd in group.commands:
            if cmd.hidden and not self.show_hidden:
                continue
            desc = []
            desc.append(f"`{cmd.qualified_name}`")
            desc.append(f"{cmd.short_doc}\n")
            embed.add_field(name=cmd.name.capitalize(),
                            value="\n".join(desc),
                            inline=False)

        self.__add_help_field(embed)
        await self.context.send(embed=embed)


    async def send_command_help(self, command: Command[Any, ..., Any], /) -> None:

        if command.clean_params:
            params = (f"<{param}>" for param in command.clean_params.keys())
            desc = f"`{command.qualified_name} {' '.join(params)}`"
        else:
            desc = f"`{command.qualified_name}`"

        embed = discord.Embed(color=discord.Color.dark_grey(),
                              title="Command help",
                              description=desc)

        if command.help:
            embed.add_field(name="Description",
                            value=f"{command.help}")

        await self.context.send(embed=embed)

