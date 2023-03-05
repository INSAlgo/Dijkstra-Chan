import discord
from discord.ext import commands
from discord.ext.commands import Context, command
import time

from main import CustomBot
from utils import IDs


class Basic(commands.Cog):

    def __init__(self, bot: CustomBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) :
        """
        Automatically gives member role to newcommers
        """
        await member.add_roles(self.bot.get_role(IDs.MEMBRE))

    @commands.command()
    async def ping(self, ctx: commands.Context):
        """Show latency in milliseconds"""
        before = time.monotonic()
        message = await ctx.send(":ping_pong: Pong")
        ping = (time.monotonic() - before) * 1000
        await message.edit(content=f"{message.content} in `{int(ping)}`ms")

async def setup(bot):
    await bot.add_cog(Basic(bot))
