from discord.ext.commands import Bot, Context, command

from bot import bot

from classes.github_client import GH_Client

# Command function :

@command()
async def sol(ctx: Context, func: str = None, *args: str) :
    gh_client: GH_Client = bot.clients["GitHub"]

    n_args = len(args)

    if func is None :
        if ctx.guild and not bot.check_perm(ctx, ["commands"]) :
            return
        await ctx.channel.send("This command needs arguments, see `!help` command for more info")
        return

    # Command to get the solution of an exercise from a website :
    if func == "get" :
        if ctx.guild and not bot.check_perm(ctx, ["commands"]) :
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
        if not bot.check_perm(ctx, roles=["admin"]) :
            return
        
        if n_args > 0 :
            await ctx.channel.send("tree command does not have parameters")

        _, msg = gh_client.reload_repo_tree()
        await ctx.channel.send(msg)
        return
    
    # (bureau) Command to change the token to access the Corrections repo :
    elif func == "token" :
        if not bot.check_perm(ctx, ["debug"], ["bureau"]) :
            return
        
        if n_args != 1 :
            await ctx.channel.send("token command has exactly one parameter : the new token")
            return

        bot.connect_client("OpenAI", args[0])


# Required setup :

async def setup(bot: Bot) :
    bot.add_command(sol)