import argparse
import asyncio
import contextlib
import pathlib
import requests
import re

import discord
from discord.ext.commands import Context, Bot, command

from bot import bot

from extensions.game.utils import *
from extensions.game import tournoi

import functions.embeding as embeding


# main command :

@command()
async def game(ctx: Context, game_name: str = None, action: str = None, *args: str):
    
    if game_name is None :
        line = f"You need to specify a game. Here is what we have for now :\n"
        game_names = ", ".join([f"`{name}`" for name in GAMES.keys()])
        await ctx.send(line + game_names)
        return

    if game_name not in GAMES:
        line = f"Unknown game `{game_name}`. Here is what we have for now :\n"
        game_names = ", ".join([f"`{name}`" for name in GAMES.keys()])
        await ctx.send(line + game_names)
        return

    game = GAMES[game_name]

    match action:

        case "help":
            await ctx.send(embed=embeding.embed_help(f"{game.cmd}_help.txt"))

        case "participants":
            if bot.check_perm(ctx, ["tournament"]):
                await ctx.send(f"Use this command in the {bot.channels['tournament'].mention} channel :wink:")
                return
            embed = discord.Embed(title=f"{game.name} tournament participants")
            embed.description = '\n'.join(f"<@{file.stem}>" for file in game.ai_dir.iterdir())
            await ctx.send(embed=embed)

        case "play":

            if ctx.guild and not bot.check_perm(ctx, ["games"]):
                await ctx.send(f"You need to send this as a DM or in {bot.channels['games'].mention}")
                return

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
                        user = bot.client.get_user(int(arg[2:-1]))
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
                        await bot.client.wait_for("reaction_add", check=check, timeout=3600)
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

        case "tournament":

            if not bot.check_perm(ctx, roles=["admin", "games"]):
                await ctx.send("Admins only can start a tournament")
                return

            scoreboard = await tournoi.main(bot.client, ctx, game, args)
            game.log_file.touch()

            embed = discord.Embed(title=f"{game.name} tournament results")

            lines = []
            for i, (ai, score) in enumerate(scoreboard):
                lines.append(f"{i+1}. {bot.client.get_user(int(ai)).mention} score : {score}")

            embed.add_field(name="Scoreboard", value='\n'.join(lines), inline=False)
            
            await ctx.send(embed=embed)

            await ctx.send(file=discord.File(game.log_file))

            game.log_file.unlink()

        
        case "submit":

            if ctx.guild:
                await ctx.send("You need to send this as a DM :wink:")
                return

            attachments = ctx.message.attachments
            if not attachments:
                await ctx.send("Missing attachment :poop:")
                return

            attachment = attachments[0]
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
        
        case "invite":

            if not bot.check_perm(ctx, roles=["admin"]):
                return
            
            user_ids = {int(file.stem) for file in game.ai_dir.iterdir()}
            guild_users = {user.id for user in ctx.guild.members}
            missing_users = user_ids.difference(guild_users)

            if missing_users:
                for user_id in missing_users:
                    ai = bot.client.get_user(user_id)
                    await ai.create_dm().send(f"Please join our server to take part in the connect4 AI tournament : {ctx.channel.create_invite(max_uses=1)}")
                    await ctx.send(f"Sent invite to {ai.mention}")
            else:
                await ctx.send(f"No missing participants on the server :thumbsup:")

        case _:
            await ctx.send(f"Unknown command. Use `game {game_name} help` for help.")


# Required setup :

async def setup(bot: Bot) :
    bot.add_command(game)