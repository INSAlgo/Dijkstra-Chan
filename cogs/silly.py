import asyncio, re

import discord
import discord.ext.commands as cmds
from utils.checks import in_channel

from main import CustomBot
from utils.ids import COMMANDS

fact = 1

class Silly(cmds.Cog, name="Silly commands"):
    """
    Silly commands
    """

    def __init__(self, bot: CustomBot):
        self.bot = bot

    async def __factorial(self, message: discord.Message, nb: int):
        "Yes, it seems that this is ugly on purpose"
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
            if word.lower().startswith("di") and len(word) > 2 + 5:
                await message.channel.send(word[2:])
                return
            if word.lower().startswith("cri") and len(word) > 3 + 5:
                await message.channel.send(word[3:].upper())
                return

    @cmds.Cog.listener()
    async def on_message(self, message: discord.Message) :
        """
        Parse every message to find if there is a silly thing to answer
        """
        
        # Self responding :

        if message.author == self.bot.user:
            if re.fullmatch(r"^\!factorial [0-9]+$", message.content) is not None:
                nb = int(message.content.split(' ')[-1])
                await self.__factorial(message, nb)

        # To prevent self response
        if message.author == self.bot.user :
            return

        # Classic silly things :

        if "di" in message.content or "cri" in message.content:
            await self.__di_cri(message)

    @cmds.command()
    @in_channel(COMMANDS)
    async def factorial(self, ctx: cmds.Context, nb: int):
        """
        Computes the factorial of a number in a very efficient way
        """
        await self.__factorial(ctx.message, nb)
        

async def setup(bot: CustomBot):
    await bot.add_cog(Silly(bot))
