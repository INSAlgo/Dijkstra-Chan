import pathlib

import discord
import discord.ext.commands as cmds
import requests
import os

from main import CustomBot
from utils.checks import in_channel
from utils.ids import *


class CodeGolf(cmds.Cog, name="Code golf"):
    """
    Commands related to a code golf contest
    """
    
    NB_CHALLENGES = 7
    FILES_PATH = pathlib.Path("saved_data/code_golf")

    def __init__(self, bot: CustomBot):
        self.bot = bot

    @cmds.group()
    async def golf(self, ctx: cmds.Context):
        """
        Commands to participate in a code golf contest
        """
        if ctx.invoked_subcommand is None:
            raise cmds.BadArgument("Invalid subcommand, see `help golf`")
    
    def challenge(argument: str) -> int:
        if argument.isnumeric() and 0 < int(argument) <= CodeGolf.NB_CHALLENGES:
            return int(argument)
        else:
            raise cmds.BadArgument(f"Input the number of the challenge ({CodeGolf.NB_CHALLENGES} available)")

    @golf.command()
    @cmds.dm_only()
    async def submit(self, ctx: cmds.Context, challenge: challenge, attachment: discord.Attachment):
        """
        Submit a program to the code golf contest.
        This command must be used in private message, with your program as an attachment.
        """

        extension = attachment.filename.split(".")[-1]
        challenge_path = CodeGolf.FILES_PATH / str(challenge)
        name = str(ctx.message.author.name)
        file = challenge_path / f"{name}.{extension}"

        if not challenge_path.is_dir():
            challenge_path.mkdir(parents=True)
        
        for previous_file in challenge_path.glob(f"{name}.*"):
            previous_file.unlink()
            await ctx.send("Your previous submission will be replaced")

        program = requests.get(attachment.url).text
        with file.open("w") as content:
            content.write(program)
        
        bytes = file.stat().st_size
        characters = len(program)

        await ctx.send(f"Program submitted! <:feelsgood:737960024390762568> {bytes} bytes / {characters} characters")

async def setup(bot: CustomBot):
    await bot.add_cog(CodeGolf(bot))