import discord.ext.commands as commands

from utils import IDs

def in_channel(*channel_ids: int) :
    async def predicate(ctx: commands.Context) :
        if ctx.channel.id in channel_ids or ctx.channel.id == IDs.DEBUG:
            return True
        channel_list = " ".join(ctx.bot.get_channel(channel_id).mention for channel_id in channel_ids)
        raise commands.CheckFailure(f"This command can be used in thoses channels: {channel_list}")
    return commands.check(predicate)
