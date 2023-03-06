import discord
from discord.ext import commands
from cogs.github import GithubClient
from utils import embeding

from main import CustomBot
from utils import ids


class Admin(commands.Cog):
    """
    Admin only commands
    """

    def __init__(self, bot: CustomBot):
        self.bot = bot

    @commands.command(hidden=True)
    @commands.has_role(ids.BUREAU)
    async def course(self, ctx: commands.Context, repo: str, course: str):
        """
        Get an embed README of a repo
        """
        github_client = self.bot.get_cog("GithubClient")
        assert isinstance(github_client, GithubClient)
        err_code, res = github_client.get_readme(repo, course)

        if err_code == 0:
            emb = embeding.embed_lesson(res).set_thumbnail(url="attachment://INSAlgo.png")
            logo = discord.File("fixed_data/INSAlgo.png", filename="INSAlgo.png")
            if ctx.channel.id == ids.DEBUG:
                channel = ctx.channel
            else:
                channel = self.bot.get_channel(ids.RESSOURCES)
            assert isinstance(channel, discord.TextChannel)
            await channel.send(file=logo, embed=emb)
        else :
            await ctx.send(res)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def shutdown(self, ctx: commands.Context) :
        """
        Shutdown the bot
        """
        await ctx.send("Shutting down ...")
        await self.bot.close()

async def setup(bot):
    await bot.add_cog(Admin(bot))
