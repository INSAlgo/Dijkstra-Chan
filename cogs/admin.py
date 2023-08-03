import logging

import discord
from discord.ext import commands

from utils.embeding import embed_lesson
from utils.github import github_client

from main import CustomBot
from utils import ids
logger = logging.getLogger(__name__)

class Admin(commands.Cog):
    """
    Admin only commands
    """

    def __init__(self, bot: CustomBot):
        self.bot = bot

    @commands.command(hidden=True)
    @commands.has_role(ids.BUREAU)
    async def lesson(self, ctx: commands.Context, repo: str = "", *, lesson: str = ""):
        """
        Get an embed from the README of a given lesson in a given repo.
        If no repo is given, takes the repo named after the current schoolyear : `INSAlgo-{year1}-{year2}`.
        If no lesson is given, takes the lesson with the highest number.
        """

        err_code, res = github_client.get_lesson_ressource(repo, lesson)

        if err_code == 0:
            emb = embed_lesson(res).set_thumbnail(url="attachment://INSAlgo.png")
            logo = discord.File("data/INSAlgo.png", filename="INSAlgo.png")
            channel = self.bot.get_channel(ids.RESSOURCES)
            assert isinstance(channel, discord.TextChannel)
            await channel.send(file=logo, embed=emb)
        
        else :
            if err_code == 5 :
                res += "\nYou can also pass the exact repo name as an argument of this function."
            if err_code == 6 :
                res += "\nYou can also pass the exact lesson (folder) name as an argument of this function."
            
            await self.bot.get_channel(ids.DEBUG).send(res)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def shutdown(self, ctx: commands.Context) :
        """
        Shutdown the bot
        """
        await ctx.send("Down")
        logger.info("shutting down")
        await self.bot.close()

async def setup(bot):
    await bot.add_cog(Admin(bot))
