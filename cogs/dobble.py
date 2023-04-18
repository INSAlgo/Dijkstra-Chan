import discord
from discord.ext import commands
from cogs.github import GithubClient

from main import CustomBot
from utils import ids

class Dobble(commands.Cog) :
    """
    Commands and functions for a game of Dobble
    """

    def __init__(self, bot: CustomBot) -> None:
        self.bot = bot
        self.cards: list[tuple[int]] = []

    @staticmethod
    def check_N(N: int) -> bool:
        """
        A number is valid for a dobble generation (with the current method) only if it's prime.
        There's a method allowing for powers of primes but I can't be fucked.
        """
        i = 2
        while i*i <= N :
            if N%i == 0 :
                return False
        return True
    
    def gen_list_cards(self, N: int) -> None:
        """
        Generates the list of cards as a list of tuples containing integers (ids of pictures)
        """

        # Grid cards :
        self.cards = []
        for c in range(N) :
            for r in range(N) :
                card = tuple((c - k*r)%N + N*k for k in range(N)) + (N*N + r,)
                self.cards.append(card)
        
        # Cards at infinity :
        for k in range(N+1) :
            self.cards.append(tuple(N*k + i for i in range(N)) + (N*(N+1),))
        
    # Commands :

    @commands.command(hidden=True)
    @commands.has_role(ids.ADMIN)
    async def geturl(self, ctx, emoji: discord.Emoji):
        await ctx.send(emoji.url)

async def setup(bot):
    await bot.add_cog(Dobble(bot))
