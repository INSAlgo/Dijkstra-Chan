import asyncio
import contextlib
import requests
import re
import argparse

import discord
from discord.ext.commands import Context
from discord.ext import commands
from utils import ids

from utils import checks
from functions.game.game_classes import AvailableGame, Ifunc, Ofunc
from functions.game import tournament

from submodules.p4 import puissance4
from auto_compiler.auto_compiler import AutoCompiler
from auto_compiler.errors import CompilerException
from main import CustomBot


class Game(commands.Cog, name="Games"):
    """
    Commands related to games
    """

    games: dict[str, AvailableGame] = dict()
    games["p4"] = AvailableGame("Connect 4", "p4", puissance4, "https://github.com/INSAlgo/Concours-Puissance4/")

    def __init__(self, bot: CustomBot):
        self.bot = bot

    @commands.group()
    async def game(self, ctx: Context):
        """
        Commands to play games with users or their handcrafted AI, and participate in tournaments
        """
        if ctx.invoked_subcommand is None:
            raise commands.BadArgument("Invalid subcommand")

    @game.command()
    async def list(self, ctx: Context):
        """
        List available games, with their prefixes and rules
        """
        embed = discord.Embed(title=f"INSAlgo tournament games")
        for game in self.games.values():
            embed.add_field(name=game.name,
                            value=f"`{game.cmd}` - [game page]({game.url})",
                            inline=False)
        await ctx.send(embed=embed)

    @game.command()
    async def participants(self, ctx: Context, game: AvailableGame):
        """
        Get the list of users who submitted an AI to the game
        """
        embed = discord.Embed(title=f"{game.name} tournament participants")
        embed.description = '\n'.join(f"<@{file.stem}>" for file in game.ai_dir.iterdir())
        await ctx.send(embed=embed)

    @game.command()
    @checks.in_channel(ids.GAMES)
    async def play(self, ctx: Context, game: AvailableGame, *args: str):
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

        for arg in remaining_args :
            if arg == "-d" or arg == "--discord":
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
                        for ai_file in game.ai_dir.glob(f"{user.id}.*"):
                            players.append(str(ai_file))
                            if user != ctx.author:
                                challenged_users.add(user)
                            break
                        else:
                            await ctx.send(f"{user.mention} has not submitted any AI :cry:")
                    is_human = False
            else:
                game_args.append(arg)

        if len(players) < 2:
            raise commands.BadArgument("Not enough players to start a game :grimacing:")

        if parsed_args.private:
            channel_type = discord.ChannelType.private_thread
            await ctx.send(f"The game will be played in the private thread :spy:")
        else:
            channel_type = discord.ChannelType.public_thread
        assert isinstance(ctx.channel, discord.TextChannel)
        thread = await ctx.channel.create_thread(name=f"{game.name} game started by {ctx.author.display_name}",
                                             type=channel_type)

        try:
            if challenged_users:
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
            game_args.extend(("--emoji", "--nodebug"))
            if ai_only:
                game_args.append("--silent")

            ofunc = Ofunc(thread)
            ifunc = Ifunc(thread, self.bot)

            with game.log_file.open("w") as file:
                with contextlib.redirect_stdout(file):
                    await game.module.main(game_args, ifunc, ofunc, discord=True)

            await thread.send(file=discord.File(game.log_file))
            game.log_file.unlink()

        finally:
            await thread.edit(archived=True, locked=True)



    @game.command(hidden=True)
    @commands.has_role(ids.BUREAU)
    async def tournament(self, ctx: Context, game: AvailableGame, *args: str):
        """
        Start a tournament between every player that have submitted an AI
        You can also append flags supported by the game.
        """
        scoreboard = await tournament.main(ctx, game, args)
        game.log_file.touch()

        embed = discord.Embed(title=f"{game.name} tournament results")

        lines = []
        for i, (ai, score) in enumerate(scoreboard):
            user = self.bot.get_user(int(str(ai)))
            assert user
            lines.append(f"{i+1}. {user.mention} score : {score}")

        embed.add_field(name="Scoreboard", value='\n'.join(lines), inline=False)
        
        await ctx.send(embed=embed)

        await ctx.send(file=discord.File(game.log_file))

        game.log_file.unlink()

    @game.command()
    @commands.dm_only()
    async def submit(self, ctx: Context, game: AvailableGame, attachment: discord.Attachment):
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
        new_submission = game.ai_dir / f"ai_{name}.{new_ext}"

        if not game.ai_dir.is_dir():
            game.ai_dir.mkdir()

        for ai_file in game.ai_dir.glob(f"ai_{name}.*"):
            await ctx.send("Your previous submission will be replaced")
            ai_file.replace(new_submission)
            break

        with new_submission.open("w") as file:
            file.write(requests.get(attachment.url).text)

        autocompiler = AutoCompiler(game.ai_dir)

        try:
            _ = await autocompiler.compile_user(f"ai_{name}")
        except CompilerException as e:
            await ctx.send("Could not compile your sumbission : "+e.message)

        await ctx.send("AI submitted (new)! <:feelsgood:737960024390762568>")

    @game.command(hidden=True)
    @commands.has_role(ids.BUREAU)
    async def invite(self, ctx: Context, game: AvailableGame):
        """
        Invite missing players of a tournament on the server
        """
        user_ids = {int(file.stem) for file in game.ai_dir.iterdir()}
        assert ctx.guild
        guild_users = {user.id for user in ctx.guild.members}
        missing_users = user_ids.difference(guild_users)

        if missing_users:
            for user_id in missing_users:
                ai = self.bot.get_user(user_id)
                assert ai 
                assert isinstance(ctx.channel, discord.TextChannel)
                await ai.create_dm().send(f"Please join our server to take part in the connect4 AI tournament : {ctx.channel.create_invite(max_uses=1)}")
                await ctx.send(f"Sent invite to {ai.mention}")
        else:
            await ctx.send(f"No missing participants on the server :thumbsup:")


async def setup(bot):
	await bot.add_cog(Game(bot))
