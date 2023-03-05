import discord.ext.commands as cmds

from utils.ids import *
from utils.checks import *

from utils.token_error import TokenError
from cogs.github import GithubClient
from main import CustomBot


class Solutions(cmds.Cog) :
    def __init__(self, bot: CustomBot) -> None:
        self.bot = bot
        self.gh_client: GithubClient = bot.get_cog("GithubClient")
    
    @cmds.group(pass_context=True)
    @in_channel(COMMANDS, force_guild=False)
    async def sol(self, ctx: cmds.Context) :
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid subcommand passed, maybe you mean `!sol get`?")

    @sol.command()
    async def help(self, ctx: cmds.Context) :
        await ctx.send("TODO :)")

    @sol.command(rest_is_raw=True)
    async def get(self, ctx: cmds.Context, site: str = "", *, file: str) :
        _, raw_message = self.gh_client.search_correction(site, file.strip())
        await ctx.channel.send(raw_message)
        return
    
    @sol.command()
    @in_channel(DEBUG)
    @cmds.has_role(ADMIN)
    async def tree(self,  ctx: cmds.Context) :
        _, msg = self.gh_client.reload_repo_tree()
        await ctx.channel.send(msg)
        return

    @sol.command()
    @in_channel(DEBUG)
    @cmds.has_role(BUREAU)
    async def token(self,  ctx: cmds.Context, token: str = None) :        
        if token is None :
            await ctx.channel.send("token command has exactly one parameter : the new token")
            return
        
        try :
            self.gh_client.set_token(token)
        except TokenError :
            await ctx.send("Invalid token !")
        except Exception as e :
            await ctx.send(f"Error : {e}")


async def setup(bot):
	await bot.add_cog(Solutions(bot))
