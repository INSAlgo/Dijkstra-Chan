import discord
from discord.ext import commands
import time

from main import CustomBot
from utils import ids


class Basic(commands.Cog):
    """
    Various basic commands
    """

    def __init__(self, bot: CustomBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) :
        """
        Automatically gives member role to newcommers
        """
        member_role = member.guild.get_role(ids.MEMBRE)
        assert member_role
        await member.add_roles(member_role)

    @commands.command()
    async def ping(self, ctx: commands.Context):
        """
        Shows latency in milliseconds
        """
        before = time.monotonic()
        message = await ctx.send(":ping_pong: Pong")
        ping = (time.monotonic() - before) * 1000
        await message.edit(content=f"{message.content} in `{int(ping)}`ms")

async def setup(bot):
    await bot.add_cog(Basic(bot))
