import logging
import discord
from discord.ext import commands
import time
from cogs.github import GithubClient
from utils import embeding

from main import CustomBot
from utils import IDs


class Admin(commands.Cog):

    def __init__(self, bot: CustomBot):
        self.bot = bot

    @commands.command()
    @commands.has_role(IDs.BUREAU)
    async def course(self, ctx: commands.Context, repo: str, course: str):
        """ Command to get README of a repo """

        github_client = self.bot.get_cog("GithubClient")
        assert isinstance(github_client, GithubClient)
        err_code, res = github_client.get_readme(repo, course)

        if err_code == 0:
            emb = embeding.embed(res).set_thumbnail(url="attachment://INSAlgo.png")
            logo = discord.File("fixed_data/INSAlgo.png", filename="INSAlgo.png")
            if ctx.channel.id == IDs.DEBUG:
                channel = ctx.channel
            else:
                channel = self.bot.get_channel(IDs.RESSOURCES)
                assert channel
            await channel.send(file=logo, embed=emb)
        else :
            await ctx.send(res)

    @commands.command()
    @commands.is_owner()
    async def shutdown(self, ctx: commands.Context) :
        await ctx.send("Shutting down ...")
        await self.bot.close()

async def setup(bot):
    await bot.add_cog(Admin(bot))
