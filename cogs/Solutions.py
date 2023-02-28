import discord.ext.commands as commands

from IDs import *
from checks import *

from classes.github_client import GH_Client

# Solutions Cog :

class SolutionsCog(commands.Cog) :
    def __init__(self, bot: commands.Bot, gh_client: GH_Client) -> None:
        self.bot = bot
        self.gh_client = gh_client
    
    @commands.group(pass_context=True, invoke_without_command=True)
    async def sol(self, ctx: commands.Context, *args) :
        print(args)
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid subcommand passed, maybe you mean `!sol get`?")

    @sol.command
    @in_channel(COMMANDS, False)
    async def get(self, ctx: commands.Context, site: str = "", *args) :
        print(args)
        n_args = len(args)
        
        if n_args == 0 :
            file = ""
        else :
            site = args[0]
            file = ' '.join(args[1:])

        _, raw_message = self.gh_client.search_correction(site, file)
        await ctx.channel.send(raw_message)
        return
    
    @sol.command
    @commands.has_role(ADMIN)
    async def tree(self,  ctx: commands.Context, site: str = "", *args) :
        print(args)
        n_args = len(args)

        if n_args > 0 :
            await ctx.channel.send("tree command does not have parameters")

        _, msg = self.gh_client.reload_repo_tree()
        await ctx.channel.send(msg)
        return

    @sol.command
    @in_channel(DEBUG)
    @commands.has_role(BUREAU)
    async def token(self,  ctx: commands.Context, site: str = "", *args) :
        print(args)
        n_args = len(args)
        
        if n_args != 1 :
            await ctx.channel.send("token command has exactly one parameter : the new token")
            return

        # bot.connect_client("OpenAI", args[0])