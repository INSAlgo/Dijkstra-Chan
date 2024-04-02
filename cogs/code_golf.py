import pathlib

import discord
import discord.ext.commands as cmds
import requests

from main import CustomBot
from utils.checks import in_channel
from utils import ids


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
        program = requests.get(attachment.url).text
        size = len(program.encode())    # size in bytes

        if not challenge_path.is_dir():
            challenge_path.mkdir(parents=True)
        
        # Overwrite previous submissions
        previous_files = tuple(challenge_path.glob(f"{name}.*"))
        if previous_files:
            best_size = min(file.stat().st_size for file in previous_files)
            if best_size < size:
                message = await ctx.send(
                    f"Your previous submission is better: {best_size} bytes < {size} bytes\n"
                    "Are you sure you want to replace it? <:chokbar:1224778767025569874>")
                await message.add_reaction("👍")
                await message.add_reaction("👎")
                
                def check(reaction: discord.Reaction, user: discord.User):
                    return user == ctx.author and reaction.message == message and reaction.emoji in ("👍", "👎")
                
                try:
                    reaction, _ = await self.bot.wait_for("reaction_add", check=check, timeout=30)
                    if reaction.emoji == "👎":
                        await ctx.send("Submission cancelled <:sad_cat:1224776278092288051>")
                        return
                except TimeoutError:
                    await ctx.send("Submission cancelled <:sad_cat:1224776278092288051>")
                    return
            
            for file in previous_files:
                file.unlink()

        
        with file.open("w") as content:
            content.write(program)
        
        bytes = file.stat().st_size
        characters = len(program)
        # TODO send a message in the code golf channel if it is a new record

        await ctx.send(f"Program submitted! <:feelsgood:737960024390762568> {bytes} bytes{f' ({characters} characters)' if characters != bytes else ''}")

    @golf.command()
    async def leaderboard(self, ctx: cmds.Context, challenge: challenge = None):
        """
        Display the leaderboard of the code golf
        """

        embed = discord.Embed(title=f"Code golf leaderboard")
        if challenge is not None:
            challenge_path = CodeGolf.FILES_PATH / str(challenge)
            leaderboard = [(file.stat().st_size, file.stem) for file in challenge_path.iterdir()]
            leaderboard.sort()
            leaderboard = "\n".join(f"{user} : {size} bytes" for size, user in leaderboard)
            embed.add_field(name=f"Challenge {challenge}", value=leaderboard, inline=False)
        else:
            embed.add_field(name=f"All challenges", value="TODO", inline=False) 

        await ctx.send(embed=embed)

async def setup(bot: CustomBot):
    await bot.add_cog(CodeGolf(bot))