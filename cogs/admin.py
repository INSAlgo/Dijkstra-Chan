from logging import getLogger
from pathlib import Path
from urllib.parse import quote

import discord
import discord.ext.commands as commands

from utils.ids import *
from utils.embeding import embed_lesson
from utils.github import github_client

from main import CustomBot


logger = getLogger(__name__)

class Admin(commands.Cog):
    """
    Admin only commands
    """

    def __init__(self, bot: CustomBot):
        self.bot = bot

    @commands.group(aliases=["re"])
    async def reload(self, ctx: commands.Context, extension: str = ""):
        """
        Reload the bot
        """
        for cog in Path("cogs").glob("*.py"):
            await self.bot.reload_extension(f"cogs.{cog.stem}")
        await ctx.send("Reloaded :rocket:")


    @commands.command(hidden=True)
    @commands.has_role(BUREAU)
    async def lesson(self, ctx: commands.Context, repo: str = "", lesson: str = ""):
        """
        Get an embed from the README of a given lesson in a given repo.
        If no repo is given, takes the repo named after the current schoolyear : `INSAlgo-{year1}-{year2}`.
        If no lesson is given, takes the lesson with the highest number.
        You can pass a lesson number for the current year, or the year of the repo followed by the lesson number, or the name of either or both.
        """

        if lesson == "" :
            lesson = repo
            repo = ""

        try:
            repo, lesson = github_client.find_lesson_ressource(repo, lesson)
            res = github_client.get_repo_readme(repo, lesson)
        except Exception as e:
            await self.bot.get_channel(DEBUG).send(str(e))

        else:
            emb = embed_lesson(res).set_thumbnail(url="attachment://INSAlgo.png")
            logo = discord.File("data/INSAlgo.png", filename="INSAlgo.png")
            channel = self.bot.get_channel(COMM_SEANCE)

            if not emb.url.startswith('http'):
                file = emb.url
                url = f"https://github.com/INSAlgo/{repo}/blob/main/{lesson}/{file}"
                emb.url = quote(url, safe=':/')

            assert isinstance(channel, discord.TextChannel)
            await channel.send(file=logo, embed=emb)



    @commands.command(aliases=["down"])
    @commands.has_role(BUREAU)
    async def shutdown(self, ctx: commands.Context) :
        """
        Shutdown the bot
        """
        await ctx.send("Down")
        logger.info("shutting down")
        await self.bot.close()


async def setup(bot: CustomBot):
    await bot.add_cog(Admin(bot))
