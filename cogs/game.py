import io
import argparse, asyncio, contextlib, re, requests
import sys
import traceback

import discord
import discord.ext.commands as cmds

# Home made auto compiler for multiple languages
from auto_compiler.auto_compiler import AutoCompiler
from auto_compiler.errors import CompilerException

import modules.game.tournament as trnmnt
from modules.game.game_classes import AvailableGame, Ifunc, Ofunc

from utils.ids import *
from utils.checks import in_channel

from main import CustomBot
from utils.multiwriter import MultiWriter


ASK_CHALLENGED_PLAYERS = False

class Game(cmds.Cog, name="Games"):
    """
    Commands related to games
    """

    def __init__(self, bot: CustomBot):
        self.bot = bot
        AvailableGame.load_games()

    @cmds.group()
    async def game(self, ctx: cmds.Context):
        """
        Commands to play games with users or their handcrafted AI, and participate in tournaments
        """
        if ctx.invoked_subcommand is None:
            raise cmds.BadArgument("Invalid subcommand, see `help game`")

    @game.command()
    async def list(self, ctx: cmds.Context):
        """
        List available games, with their prefixes and rules
        """
        AvailableGame.load_games()
        embed = discord.Embed(title="INSAlgo tournament games")
        for game in AvailableGame.games:
            embed.add_field(name=game.name,
                    value=f"`{game.cmd}` - [game page]({game.url})",
                    inline=False)
        await ctx.send(embed=embed)

    @game.command()
    async def participants(self, ctx: cmds.Context, game: AvailableGame):
        """
        Get the list of users who submitted an AI to the game
        """
        embed = discord.Embed(title=f"{game.name} tournament participants")
        ids = [file.stem[3:] for file in game.ai_path.iterdir() if file.stem.startswith('ai_')]
        embed.description = '\n'.join(f"<@{id}>" for id in ids)
        await ctx.send(embed=embed)

    @game.command()
    @in_channel(GAMES)
    async def play(self, ctx: cmds.Context, game: AvailableGame, *args: str):
        """
        Play a game between AI or users if available
        Specify the list of players in the <args> by mentionning them. \
        If you want a player to play on manually on discord instead of using their AI, \
        add the flag -d (or --discord) before their name. \
        You can play in private channel by adding the 
        You can also append any other flag that the game supports (see the game page).
        """
        
        parser = argparse.ArgumentParser()
        parser.add_argument("--private", action="store_true")
        parsed_args, remaining_args = parser.parse_known_args(args)

        game_args = []
        players = []
        pattern = re.compile(r"^\<\@[0-9]{18}\>$")
        ai_only = True
        is_human = False
        challenged_users: set[discord.User] = set()

        for arg in remaining_args:
            if arg in ["-d", "--discord"]:
                is_human = True
                continue
            if pattern.match(arg):
                user = self.bot.get_user(int(arg[2:-1]))
                if user:
                    if is_human:
                        players.append(arg)
                        if user != ctx.author:
                            challenged_users.add(user)
                        ai_only = False
                    else:
                        for ai_file in game.ai_path.glob(f"ai_{user.id}*"):
                            players.append(str(ai_file))
                            if user != ctx.author:
                                challenged_users.add(user)
                            break
                        else:
                            await ctx.send(f"{user.mention} has not submitted any AI :cry:")
                            return
                    is_human = False
            else:
                game_args.append(arg)

        if len(players) < 2:
            raise cmds.BadArgument("Not enough players to start a game :grimacing:")

        if parsed_args.private:
            channel_type = discord.ChannelType.private_thread
            await ctx.send("The game will be played in the private thread :spy:")
        else:
            channel_type = discord.ChannelType.public_thread
        assert isinstance(ctx.channel, discord.TextChannel)
        thread = await ctx.channel.create_thread(name=f"{game.name} game started by {ctx.author.display_name}",
                                             type=channel_type)

        try:
            if ASK_CHALLENGED_PLAYERS and challenged_users:
                message = await thread.send(f"{', '.join(user.mention for user in challenged_users)}" +
                                         f" do you accept {ctx.author.mention}'s challenge to a game of {game.name} ?")
                await message.add_reaction("👍")
                for user in challenged_users:

                    def check(reaction: discord.Reaction, user: discord.User):
                        return user in challenged_users and str(reaction.emoji) in ("👍")

                    try:
                        count = 0
                        while count < len(challenged_users):
                            await self.bot.wait_for("reaction_add", check=check, timeout=60)
                            count += 1
                    except asyncio.TimeoutError:
                        await thread.send("Waited too long for the game to start, giving up")
                        return 

            game_args.extend(players)
            # game_args.extend(("--emoji", "--nodebug"))
            if ai_only:
                game_args.append("--silent")

            ofunc = Ofunc(thread)
            ifunc = Ifunc(thread, self.bot)

            file = io.StringIO()
            try:
                writer = MultiWriter(lambda *args, **kwargs:file.write(*args), sys.stdout.write)
                with contextlib.redirect_stdout(writer):
                    with contextlib.redirect_stderr(writer):
                        await game.module.main(game_args, ifunc, ofunc, discord=True)

            except Exception:
                traceback.print_exc()
                raise
            except SystemExit:
                # Might happen if wrong arguments are passed
                traceback.print_exc()

            file.seek(0)
            raw_file = io.BytesIO(file.read().encode())
            await thread.send(file=discord.File(raw_file, filename="game_log.txt"))

        finally:
            await thread.edit(archived=True, locked=True)


    @game.command(hidden=True)
    @cmds.has_role(BUREAU)
    async def tournament(self, ctx: cmds.Context, game: AvailableGame, *args: str):
        """
        Start a tournament between every player that have submitted an AI
        You can also append flags supported by the game.
        """
        scoreboard = await trnmnt.main(ctx, game, args)
        game.log_file.touch()

        embed = discord.Embed(title=f"{game.name} tournament results")

        lines = []
        for i, (ai, score) in enumerate(scoreboard):
            if ai.startswith("ai_"):
                ai = ai[3:]
            user = self.bot.get_user(int(str(ai)))
            assert user
            lines.append(f"{i+1}. {user.mention} score : {score}")

        embed.add_field(name="Scoreboard", value='\n'.join(lines), inline=False)
        
        await ctx.send(embed=embed)

        await ctx.send(file=discord.File(game.log_file), silent=True)

        game.log_file.unlink()

    @game.command()
    @cmds.dm_only()
    async def submit(self, ctx: cmds.Context, game: AvailableGame, attachment: discord.Attachment):
        """
        Submit an AI to a game
        This command must be used in private message, with your program as an attachment.
        Authorized languages are :
         - python (.py)
         - javascript (.js)
         - C++ (.cpp)
         - C (.c)
         - Java (.java)
         - C# (.cs)
         - Rust (.rs)
        """
        new_ext = attachment.filename.split(".")[-1]
        name = str(ctx.message.author.id)
        new_submission = game.submit_path / f"ai_{name}.{new_ext}"

        if not game.submit_path.is_dir():
            game.submit_path.mkdir()

        for submit_file in game.submit_path.glob(f"ai_{name}.*"):
            await ctx.send("Your previous submission will be replaced")
            submit_file.replace(new_submission)
            break

        for ai_file in game.ai_path.glob(f"ai_{name}*"):
            ai_file.unlink()
            break

        with new_submission.open("w") as file:
            file.write(requests.get(attachment.url).text)

        autocompiler = AutoCompiler(game.submit_path, game.compile_path, game.ai_path)

        try:
            _ = await autocompiler.compile_user(f"ai_{name}")
        except CompilerException as e:
            await ctx.send(f"Could not compile your sumbission:\n```\n{e}\n```")

        await ctx.send("AI submitted (new)! <:feelsgood:737960024390762568>")

    @game.command(hidden=True)
    @cmds.has_role(BUREAU)
    async def invite(self, ctx: cmds.Context, game: AvailableGame):
        """
        Invite missing players of a tournament on the server
        """
        user_ids = {int(file.stem[3:]) for file in game.ai_path.iterdir() if file.stem.startwith("ai_")}
        assert ctx.guild
        guild_users = {user.id for user in ctx.guild.members}
        if missing_users := user_ids.difference(guild_users):
            for user_id in missing_users:
                ai = self.bot.get_user(user_id)
                assert ai 
                assert isinstance(ctx.channel, discord.TextChannel)
                await ai.create_dm().send(f"Please join our server to take part in the AI tournament : {ctx.channel.create_invite(max_uses=1)}")
                await ctx.send(f"Sent invite to {ai.mention}")
        else:
            await ctx.send("No missing participants on the server :thumbsup:")


async def setup(bot: CustomBot):
	await bot.add_cog(Game(bot))
