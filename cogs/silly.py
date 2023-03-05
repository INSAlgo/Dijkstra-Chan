import discord
from discord.ext import commands
from discord.ext.commands import Context, command
import re
from utils import checks
import asyncio

from main import CustomBot
from utils import IDs

fact = 1

class Silly(commands.Cog, name="Silly commands"):

    def __init__(self, bot: CustomBot):
        self.bot = bot

    async def __factorial(self, message: discord.Message, nb: int):
        global fact
        if nb < 0 :
            await message.channel.send("number cannot be negative !")
        elif nb > 20 :
            await message.channel.send(f"!factorial {nb-1}\njust joking, I'm not doing that")
        elif nb <= 1 :
            await message.channel.send(f"result : {fact}")
            fact = 1
        else :
            fact *= nb
            await asyncio.sleep(1)
            await message.channel.send(f"!factorial {nb-1}")
        return

    async def __di_cri(self, message: discord.Message):
        for word in message.content.split():
            if word.lower().startswith("di") and len(word) > 2:
                await message.channel.send(word[2:])
                return
            if word.lower().startswith("cri") and len(word) > 3:
                await message.channel.send(word[3:].upper())
                return

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) :
        """
        Automatically gives member role to newcommers
        """
        if message.author == self.bot.user:
            if re.fullmatch(r"^\!factorial [0-9]+$", message.content) is not None:
                nb = int(message.content.split(' ')[-1])
                await self.__factorial(message, nb)

        if "di" in message.content or "cri" in message.content:
            await self.__di_cri(message)

    @commands.command()
    @checks.in_channel(IDs.COMMANDS)
    async def factorial(self, ctx: commands.Context, nb: int):
        """
        Compute the factorial of a number in a very efficient way
        """
        await self.__factorial(ctx.message, nb)
        

async def setup(bot):
    await bot.add_cog(Silly(bot))
