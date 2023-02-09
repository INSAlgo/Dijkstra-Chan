import discord
from discord.ext.commands import Context

from classes.github_client import GH_Client

async def command_(
        gh_client: GH_Client,
        bureau_role: discord.Role, admin_role: discord.Role,
        debug_channel: discord.TextChannel, command_channels: set[discord.TextChannel], 
        ctx: Context, func: str, *args: str
    ) :
    n_args = len(args)

    if func is None :
        if ctx.guild and (ctx.channel not in command_channels) :
            return
        ctx.channel.send("This command needs arguments, see help command for more info")
        return

    # Command to get the solution of an exercise from a website :
    if func == "get" :
        if ctx.guild and (ctx.channel not in command_channels) :
            return
        
        if n_args == 0 :
            site = ""
            file = ""
        elif n_args == 1 :
            site = args[0]
            file = ""
        else :
            site = args[0]
            file = ' '.join(args[1:])

        _, raw_message = gh_client.search_correction(site, file)
        await ctx.channel.send(raw_message)
        return
    
    # (admin) Command to reload the cache of the Corrections repo tree :
    elif func == "tree" :
        if admin_role not in ctx.author.roles :
            return
        
        if n_args > 0 :
            await ctx.channel.send("tree command does not have parameters")

        _, msg = gh_client.reload_repo_tree()
        await ctx.channel.send(msg)
        return
    
    # (bureau) Command to change the token to access the Corrections repo :
    elif func == "token" :
        if bureau_role not in ctx.author.roles or ctx.channel != debug_channel :
            return
        
        if n_args != 1 :
            await ctx.channel.send("token command has exactly one parameter : the new token")
            return

        return args[0]