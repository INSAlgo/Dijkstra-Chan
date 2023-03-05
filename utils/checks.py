import discord.ext.commands as commands

from utils import IDs

def in_channel(*channel_ids: int, force_guild=True) :
    async def predicate(ctx: commands.Context) :
        if not force_guild and ctx.guild is None :
            return True
        if ctx.channel.id in channel_ids or ctx.channel.id == IDs.DEBUG:
            return True
        
        channel_list = [f"<#{channel_id}>" for channel_id in channel_ids]
        if not force_guild :
            channel_list.append("or in DM :smirk:")
        raise commands.CheckFailure(f"This command can be used in thoses channels: {' '.join(channel_list)}")
    
    return commands.check(predicate)
