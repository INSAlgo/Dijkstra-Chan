
import discord
import discord.ext.commands as cmds

from utils.IDs import *
from utils.checks import *

# Events reminders Cog :

class EventRemind(cmds.Cog) :
    def __init__(self, bot: cmds.Bot) -> None:
        self.bot = bot
        self.event_role: discord.Role = None

    @cmds.group(pass_context=True)
    @in_channel(COMMANDS, False)
    async def evt(self, ctx: cmds.Context) :
        if ctx.invoked_subcommand is None:
            await ctx.send(f"Invalid subcommand, see `!evt help`.")
    
    @evt.command()
    async def toggle(self, ctx: cmds.Context) :
        msg = "Role successfully "
        if self.event_role in ctx.author.roles :
            await ctx.author.remove_roles(self.event_role)
            msg += "removed."
        else :
            await ctx.author.add_roles(self.event_role)
            msg += "given."
        await ctx.channel.send(msg)