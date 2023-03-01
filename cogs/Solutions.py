import discord.ext.commands as cmds

from utils.IDs import *
from utils.checks import *

from utils.token_error import TokenError
from cogs.Github_Client import GH_ClientCog

# Solutions Cog :

class SolutionsCog(cmds.Cog) :
    def __init__(self, bot: cmds.Bot) -> None:
        self.gh_client: GH_ClientCog = bot.get_cog("GH_ClientCog")
    
    @cmds.group(pass_context=True)
    async def sol(self, ctx: cmds.Context) :
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid subcommand passed, maybe you mean `!sol get`?")

    @sol.command()
    async def help(self, ctx: cmds.Context) :
        await ctx.send("TODO :)")

    @sol.command(rest_is_raw=True)
    @in_channel(COMMANDS, False)
    async def get(self, ctx: cmds.Context, site: str = "", *, file: str) :
        _, raw_message = self.gh_client.search_correction(site, file.strip())
        await ctx.channel.send(raw_message)
        return
    
    @sol.command()
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