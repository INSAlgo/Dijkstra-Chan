import time

import discord
import discord.ext.commands as cmds

from utils.ids import MEMBRE

from main import CustomBot


class Basic(cmds.Cog):
    """
    Various basic cmds
    """

    @cmds.Cog.listener()
    async def on_member_join(self, member: discord.Member) :
        """
        Automatically gives member role to newcommers
        """
        member_role = member.guild.get_role(MEMBRE)
        assert member_role
        await member.add_roles(member_role)

    @cmds.command()
    async def ping(self, ctx: cmds.Context):
        """
        Shows latency in milliseconds
        """
        before = time.monotonic()
        message = await ctx.send(":ping_pong: Pong")
        ping = (time.monotonic() - before) * 1000
        await message.edit(content=f"{message.content} in `{int(ping)}`ms")

async def setup(bot: CustomBot):
    await bot.add_cog(Basic())
