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
    
    ONGOING = False
    FILES_PATH = pathlib.Path("saved_data/code_golf_2024")
    REFERENCE_IMPLEM = "everyone"
    EXTENSIONS = {
        "py": "Python",
        "c": "C",
        "cpp": "C++",
        "java": "Java",
        "js": "JavaScript",
        "rs": "Rust",
        "hs": "Haskell",
        "pl": "Perl/Prolog",
        "sh": "Shell",
        "go": "Go",
        "cs": "C#",
        "kt": "Kotlin",
        "php": "PHP",
        "lua": "Lua",
        "rb": "Ruby",
        "ml": "OCaml",
        "zig": "Zig",
        "nim": "Nim",
        "ua": "Uiua",
        "sage": "Sage",
    }

    def __init__(self, bot: CustomBot):
        self.bot = bot


    @cmds.group()
    async def golf(self, ctx: cmds.Context):
        """
        Commands to participate in a code golf contest
        """
        if not CodeGolf.FILES_PATH.exists():
            CodeGolf.FILES_PATH.mkdir()
        if ctx.invoked_subcommand is None:
            raise cmds.BadArgument("Invalid subcommand, see `help golf`")
    

    def challenge(argument: str) -> str:
        path = CodeGolf.FILES_PATH / argument
        if path.is_dir():
            return argument
        else:
            challenges = ", ".join(f"{dir.name}" for dir in sorted(CodeGolf.FILES_PATH.iterdir()) if dir.is_dir())
            raise cmds.BadArgument(f"{argument} is not a valid challenge. Available challenges are: {challenges}" )

    def challenges(arguments: str) -> str:
        challenges = []
        for argument in arguments.split(","):
            if argument:
                challenges.append(CodeGolf.challenge(argument))
        return challenges

    @golf.command(aliases=["ref"], hidden=True)
    @cmds.has_role(ids.BUREAU)
    async def reference(self, ctx: cmds.Context, challenge: str, attachment: discord.Attachment):
        """
        Submit a reference implementation for a code golf challenge
        """
        challenge_path = CodeGolf.FILES_PATH / challenge
        if not challenge_path.is_dir():
            await ctx.send(f"Created challenge {challenge}")
            challenge_path.mkdir()

        for file in challenge_path.glob(f"{CodeGolf.REFERENCE_IMPLEM}.*"):
            file.unlink()

        extension = attachment.filename.split(".")[-1]
        file = challenge_path / f"{CodeGolf.REFERENCE_IMPLEM}.{extension}"
        program = requests.get(attachment.url).text
        with file.open("w") as content:
            content.write(program)

        await ctx.send(f"Reference implementation of challenge {challenge} saved :ok_hand:")


    @golf.command(aliases=["sub"])
    @cmds.dm_only()
    async def submit(self, ctx: cmds.Context, challenge: challenge, attachment: discord.Attachment):
        """
        Submit a program to the code golf contest.
        This command must be used in private message, with your program as an attachment.
        """

        if not CodeGolf.ONGOING:
            await ctx.send("The contest has ended, you can no longer submit :face_in_clouds:")
            return
        
        if "." not in attachment.filename:
            await ctx.send("Missing file extension, I can't tell the language of your program :confused:")
            return

        extension = attachment.filename.split(".")[-1]
        challenge_path = CodeGolf.FILES_PATH / challenge
        name = str(ctx.message.author.name)
        submission: pathlib.Path = challenge_path / f"{name}.{extension}"
        
        best_size, best_name = min((file.stat().st_size, file.stem) for file in challenge_path.iterdir())

        # Overwrite previous submissions
        previous_files = tuple(challenge_path.glob(f"{name}.*"))
        if previous_files:
            previous_size = min(file.stat().st_size for file in previous_files)
            if previous_size < attachment.size:
                message = await ctx.send(
                    f"Your previous submission is better: {previous_size} bytes < {attachment.size} bytes\n"
                    "Are you sure you want to replace it? <:chokbar:1224778687375741051>")
                await message.add_reaction("👍")
                await message.add_reaction("👎")
                
                def check(reaction: discord.Reaction, user: discord.User):
                    return user == ctx.author and reaction.message == message and reaction.emoji in ("👍", "👎")
                
                try:
                    reaction, _ = await self.bot.wait_for("reaction_add", check=check, timeout=30)
                    if reaction.emoji == "👎":
                        await ctx.send("Submission cancelled <:sad_cat:737953393816895549>")
                        return
                except TimeoutError:
                    await ctx.send("Submission cancelled <:sad_cat:737953393816895549>")
                    return
            
            for file in previous_files:
                file.unlink()

        # Save new submission
        await attachment.save(submission)
        
        size = submission.stat().st_size
        await ctx.send(f"Program submitted! {size} bytes <:feelsgood:737960024390762568> ")

        # Send message if new record
        code_golf_channel = self.bot.get_channel(ids.CODE_GOLF)
        if size < best_size:
            best_author = discord.utils.get(code_golf_channel.guild.members, name=best_name)
            best_name = best_author.mention if best_author else best_name
            await code_golf_channel.send(
                (f"{ctx.author.mention} has just beaten the record on challenge {challenge} with {size} bytes! :golf:\n"
                f"Previous record holder: {best_name} with {best_size} bytes")
            )
        
        # Add role Code Golf to author
        guild = discord.utils.get(self.bot.guilds, id=ids.INSALGO)
        member = discord.utils.get(guild.members, id=ctx.message.author.id)
        if member:
            code_golf = discord.utils.get(guild.roles, id=ids.CODE_GOLF_ROLE)
            await member.add_roles(code_golf)


    @golf.command(aliases=["sb"])
    @cmds.guild_only()
    async def scores(self, ctx: cmds.Context, challenges: challenges):
        """
        Display the scoreboard of a code golf challenge
        """

        embed = discord.Embed(title=f"Code golf scoreboard :golf:")

        for challenge in challenges:
            challenge_path = CodeGolf.FILES_PATH / challenge
            submissions = [(file.stat().st_size, file.stat().st_mtime, file) for file in challenge_path.iterdir()]
            submissions.sort()

            text = []
            for i, submission in enumerate(submissions):
                size, _, file = submission
                name, extension = file.stem, file.suffix[1:]
                language = CodeGolf.EXTENSIONS[extension] if extension in CodeGolf.EXTENSIONS else extension
                
                member = discord.utils.get(ctx.guild.members, name=name)
                mention = member.mention if member else name
                if name == CodeGolf.REFERENCE_IMPLEM:
                    mention = ctx.guild.default_role
                bureau = discord.utils.get(ctx.guild.roles, id=ids.BUREAU)

                if member and bureau in member.roles:
                    mention = f"~~{mention}~~"
                
                line = f"{i}. {mention} : {size} bytes ({language})"
                
                if member and bureau in member.roles:
                    line = f"{line} {bureau.mention}"

                text.append(line)

            embed.add_field(name=f"Challenge {challenge}", value="\n".join(text), inline=False)
            
        await ctx.send(embed=embed, silent=True)


    @golf.command(aliases=["lead", "lb"])
    @cmds.guild_only()
    async def leaderboard(self, ctx: cmds.Context):
        """
        Display the leaderboard of of the code golf contest
        """
        embed = discord.Embed(title=f"Code golf contest :golf:")
        
        participants = set(file.stem for file in CodeGolf.FILES_PATH.glob("*/*"))
        
        sizes = {participant: 0 for participant in participants}
        chall_count = {participant: 0 for participant in participants}
        
        for challenge_dir in CodeGolf.FILES_PATH.iterdir():
            if not challenge_dir.is_dir() or not len(tuple(challenge_dir.iterdir())):
                continue
        
            try:
                reference_file = next(challenge_dir.glob(f"{CodeGolf.REFERENCE_IMPLEM}.*"))
                default_size = reference_file.stat().st_size
            except StopIteration:
                default_size = max(file.stat().st_size for file in challenge_dir.iterdir())
 

            chall_sizes = {participant: default_size for participant in participants}
        
            for file in challenge_dir.iterdir():
                participant = file.stem
                chall_sizes[participant] = file.stat().st_size
                chall_count[participant] += 1
        
            for participant, chall_size in chall_sizes.items():
                sizes[participant] += chall_size

        leaderboard = []
        for participant in participants:
            leaderboard.append((sizes[participant], chall_count[participant], participant))
        leaderboard.sort()

        text = []
        for i, item in enumerate(leaderboard):
            size, count, name = item
            mention = name

            member = discord.utils.get(ctx.guild.members, name=name)
            mention = member.mention if member else name
            if name == CodeGolf.REFERENCE_IMPLEM:
                mention = ctx.guild.default_role
                count = 0
            bureau = discord.utils.get(ctx.guild.roles, id=ids.BUREAU)

            if member and bureau in member.roles:
                mention = f"~~{mention}~~"
            
            line = f"{i}. {mention} : {size} bytes ({count} challenge{'s' if count > 1 else ''})"

            if member and bureau in member.roles:
                line = f"{line} {bureau.mention}"

            text.append(line)

        embed.add_field(name=f"Leaderboard", value="\n".join(text), inline=False)
        await ctx.send(embed=embed, silent=True)


async def setup(bot: CustomBot):
    await bot.add_cog(CodeGolf(bot))