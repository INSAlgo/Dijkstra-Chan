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

    @commands.command(hidden=True, rest_is_raw=True)
    @commands.has_role(ids.BUREAU)
    async def lesson(self, ctx: commands.Context, repo: str = "", *, lesson: str = ""):
        """
        Get an embed from the README of a given lesson in a given repo.
        If no repo is given, takes the repo named after the current schoolyear : `INSAlgo-{year1}-{year2}`.
        If no lesson is given, takes the lesson with the highest number.
        """
        github_client = self.bot.get_cog("GithubClient")
        print("type github_client :", type(github_client))
        print("class github_client :", github_client.__class__)
        print("repr GithubClient :", GithubClient)
        print("type of github_client is GithubClient :", type(github_client) == GithubClient)
        print("class of github_client is GithubClient :", github_client.__class__ == GithubClient)
        assert isinstance(github_client, GithubClient) # never passes for some reason, even tho type(github_client) is fine.
        err_code, res = github_client.get_lesson_ressource(repo, lesson.strip())

        if err_code == 0:
            emb = embeding.embed_lesson(res).set_thumbnail(url="attachment://INSAlgo.png")
            logo = discord.File("fixed_data/INSAlgo.png", filename="INSAlgo.png")
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
        await ctx.send("Shutting down ...")
        await self.bot.close()

async def setup(bot):
    await bot.add_cog(Admin(bot))
