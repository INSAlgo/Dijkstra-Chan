import discord.ext.commands as cmds

from utils.checks import *
from utils.ids import *
from utils.token_error import TokenError
from utils.github import github_client


class Solutions(cmds.Cog) :
    """
    Commands related to exercises corrections
    """
    
    @cmds.group(pass_context=True)
    @in_channel(COMMANDS, force_guild=False)
    async def sol(self, ctx: cmds.Context) :
        """
        Commands to fetch solutions of exercises documented by INSAlgo
        """
        if ctx.invoked_subcommand is None:
            raise cmds.BadArgument("Invalid subcommand. Use `!help sol` for details")

    @sol.command()
    async def get(self, ctx: cmds.Context, site: str = "", *, file: str) :
        """
        Fetches a solution of any exercise we have documented
        You need to specify the website before an exercise name, use `!sol get` to see available websites
        """
        _, raw_message = github_client.search_correction(site, file)
        await ctx.channel.send(raw_message)
        return
    
    @sol.command(hidden=True)
    @in_channel(DEBUG)
    @cmds.has_role(ADMIN)
    async def tree(self,  ctx: cmds.Context) :
        """
        Refreshes the cache of the corrections repo
        You need to run this command every time new files are added to the repo, else people won't be able to access them through me
        (TODO : setup a cmds.loop for a daily refresh)
        """

        _, msg = github_client.reload_repo_tree()
        await ctx.channel.send(msg)
        return

    @sol.command(hidden=True)
    @in_channel(DEBUG)
    @cmds.has_role(BUREAU)
    async def token(self,  ctx: cmds.Context, token: str = None) :
        """
        Command to change the github token to access the corrections repo
        This token needs to be renewed regularly
        Please check my README for info on how to generate a new one on github
        """

        if token is None :
            await ctx.channel.send("token command has exactly one parameter : the new token")
            return
        
        try :
            github_client.set_token(token)
        except TokenError :
            await ctx.send("Invalid token !")
        except Exception as e :
            await ctx.send(f"Error : {e}")


async def setup(bot):
	await bot.add_cog(Solutions())
