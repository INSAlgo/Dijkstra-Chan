import discord.ext.commands as commands

from IDs import *
from checks import *

from utils.token_error import TokenError
from cogs.Github_Client import GH_ClientCog

# Solutions Cog :

class SolutionsCog(commands.Cog) :
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.gh_client: GH_ClientCog = bot.get_cog("GH_ClientCog")
    
    @commands.group(pass_context=True)
    async def sol(self, ctx: commands.Context) :
        # print(args)
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid subcommand passed, maybe you mean `!sol get`?")

    @sol.command(pass_context=True)
    @in_channel(COMMANDS, False)
    async def get(self, ctx: commands.Context, site: str = "", *args) :
        file = ' '.join(args)

        _, raw_message = self.gh_client.search_correction(site, file)
        await ctx.channel.send(raw_message)
        return
    
    @sol.command(pass_context=True)
    @commands.has_role(ADMIN)
    async def tree(self,  ctx: commands.Context) :
        _, msg = self.gh_client.reload_repo_tree()
        await ctx.channel.send(msg)
        return

    @sol.command(pass_context=True)
    @in_channel(DEBUG)
    @commands.has_role(BUREAU)
    async def token(self,  ctx: commands.Context, token: str = None) :        
        if token is None :
            await ctx.channel.send("token command has exactly one parameter : the new token")
            return
        
        try :
            self.gh_client.set_token(token)
        except TokenError :
            await ctx.send("Invalid token !")
        except Exception as e :
            await ctx.send(f"Error : {e}")