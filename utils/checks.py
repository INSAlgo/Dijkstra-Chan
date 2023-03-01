from typing import Iterable

import discord.ext.commands as commands

from utils.IDs import DEBUG

def in_channel(channel_id: int, ensure_guild = True, allow_debug = True) :
    async def predicate(ctx: commands.Context) :
        if allow_debug :
            good_channel = ctx.channel.id in {channel_id, DEBUG}
        else :
            good_channel = ctx.channel.id == channel_id

        if ensure_guild :
            return ctx.guild is not None and good_channel
        return ctx.guild is None or good_channel
    return commands.check(predicate)

def in_channels(channel_ids: Iterable[int], ensure_guild = True, allow_debug = True) :
    channel_ids = set(channel_ids)
    async def predicate(ctx: commands.Context) :
        if allow_debug :
            channel_ids.add(DEBUG)
        good_channel = (ctx.channel.id in channel_ids)

        if ensure_guild :
            return ctx.guild is not None and good_channel
        return ctx.guild is None or good_channel
    return commands.check(predicate)