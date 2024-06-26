from logging import getLogger
from pathlib import Path

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
        """

        err_code, res = github_client.get_lesson_ressource(repo, lesson)

        if err_code == 0:
            emb = embed_lesson(res).set_thumbnail(url="attachment://INSAlgo.png")
            logo = discord.File("data/INSAlgo.png", filename="INSAlgo.png")
            channel = self.bot.get_channel(RESSOURCES)
            assert isinstance(channel, discord.TextChannel)
            await channel.send(file=logo, embed=emb)
        
        else :
            if err_code == 5 :
                res += "\nYou can also pass the exact repo name as an argument of this function."
            if err_code == 6 :
                res += "\nYou can also pass the exact lesson (folder) name as an argument of this function."
            
            await self.bot.get_channel(DEBUG).send(res)


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
