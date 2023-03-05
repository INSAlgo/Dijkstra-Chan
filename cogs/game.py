import asyncio
import contextlib
import requests
import re

import discord
from discord.ext.commands import Context
from discord.ext import commands
from utils import IDs

from utils import embeding, checks
from utils.game import AvailableGame, Ifunc, Ofunc
from functions import tournament

from submodules.p4 import puissance4
from main import CustomBot


class Game(commands.Cog):

    games = dict()
    games["p4"] = AvailableGame("Connect 4", "p4", puissance4)

    def __init__(self, bot: CustomBot):
        self.bot = bot

    @commands.group()
    async def game(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            raise commands.BadArgument("Invalid subcommand")

    @game.command()
    async def help(self, ctx: Context, game: AvailableGame | None):
        if game:
            await ctx.send(embed=embeding.embed_help(f"{game.cmd}_help.txt"))
        else:
            await ctx.send("Global game help coming soon")

    @game.command()
    @checks.in_channel(IDs.GAMES)
    async def participants(self, ctx: Context, game: AvailableGame):

        embed = discord.Embed(title=f"{game.name} tournament participants")
        embed.description = '\n'.join(f"<@{file.stem}>" for file in game.ai_dir.iterdir())
        await ctx.send(embed=embed)

    @game.command()
    async def play(self, ctx: Context, game: AvailableGame, *args: str):

        game_args = []
        players = []
        pattern = re.compile(r"^\<\@[0-9]{18}\>$")
        ai_only = True
        is_human = False
        challenged_users: set[discord.User] = set()

        for arg in args:
            if arg == "-d" or arg == "--discord":
                is_human = True
                continue
            if not arg.startswith("-"):
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
                    await ctx.send(f"Invalid argument {arg} :face_with_raised_eyebrow:")
                    return

        if len(players) < 2:
            await ctx.send("Not enough players to start a game :grimacing:")
            return

        for user in challenged_users:
            message = await ctx.send(f"{', '.join(user.mention for user in challenged_users)}" +
                                     f" do you accept {ctx.author.mention}'s challenge to a game of {game.name} ?")
            await message.add_reaction("👍")

            def check(reaction: discord.Reaction, user: discord.User):
                return user in challenged_users and str(reaction.emoji) in ("👍")

            try:
                count = 0
                while count < len(challenged_users):
                    await self.bot.wait_for("reaction_add", check=check, timeout=3600)
                    count += 1
            except asyncio.TimeoutError:
                return

        game_args.extend(players)
        game_args.extend(("--emoji", "--nodebug"))
        if ai_only:
            game_args.append("--silent")

        ofunc = Ofunc(ctx.channel)
        ifunc = Ifunc(ctx.channel)

        with game.log_file.open("w") as file:
            with contextlib.redirect_stdout(file):
                await game.module.main(game_args, ifunc, ofunc, discord=True)

        await ctx.send(file=discord.File(game.log_file))
        game.log_file.unlink()


    @game.command()
    @commands.has_role(IDs.BUREAU)
    async def tournament(self, ctx: Context, game: AvailableGame, *args: str):

        scoreboard = await tournament.tournament.main(ctx, game, args)
        game.log_file.touch()

        embed = discord.Embed(title=f"{game.name} tournament results")

        lines = []
        for i, (ai, score) in enumerate(scoreboard):
            user = self.bot.get_user(int(ai))
            assert user
            lines.append(f"{i+1}. {user.mention} score : {score}")

        embed.add_field(name="Scoreboard", value='\n'.join(lines), inline=False)
        
        await ctx.send(embed=embed)

        await ctx.send(file=discord.File(game.log_file))

        game.log_file.unlink()

    @game.command()
    @commands.dm_only()
    async def submit(self, ctx: Context, game: AvailableGame, attachment: discord.Attachment):

        new_ext = attachment.filename.split(".")[-1]
        name = str(ctx.message.author.id)
        new_submission = game.ai_dir / f"{name}.{new_ext}"

        if not game.ai_dir.is_dir():
            game.ai_dir.mkdir()

        for ai_file in game.ai_dir.glob(f"{name}.*"):
            await ctx.send("Your previous submission will be replaced")
            ai_file.replace(new_submission)
            break
        
        with new_submission.open("w") as file:
            file.write(requests.get(attachment.url).text)

        await ctx.send("AI submitted ! <:feelsgood:737960024390762568>")

    @game.command()
    @commands.has_role(IDs.BUREAU)
    async def invite(self, ctx: Context, game: AvailableGame):

        user_ids = {int(file.stem) for file in game.ai_dir.iterdir()}
        assert ctx.guild
        guild_users = {user.id for user in ctx.guild.members}
        missing_users = user_ids.difference(guild_users)

        if missing_users:
            for user_id in missing_users:
                ai = self.bot.get_user(user_id)
                assert ai 
                await ai.create_dm().send(f"Please join our server to take part in the connect4 AI tournament : {ctx.channel.create_invite(max_uses=1)}")
                await ctx.send(f"Sent invite to {ai.mention}")
        else:
            await ctx.send(f"No missing participants on the server :thumbsup:")


async def setup(bot):
	await bot.add_cog(Game(bot))
