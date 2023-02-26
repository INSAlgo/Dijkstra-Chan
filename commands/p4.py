import argparse
from contextlib import redirect_stdout
import os
import pathlib
from matplotlib.rcsetup import validate_any
import io
from requests import get
import re

import discord
from discord.ext.commands import Context, Bot

from classes.p4Game import P4Game, Player
from functions.embeding import embed_help
from puissance4.puissance4 import User, AI, game
import puissance4.tournoi
import puissance4.puissance4

# Connect 4 games setup :
BOT_DIR = pathlib.Path().cwd()
GAME_DIR = BOT_DIR / "puissance4"
AI_DIR = GAME_DIR / "ai"
LOG_FILE = GAME_DIR / "log.txt"

games: list[P4Game] = []

# bot client from main script
bot: Bot

def fetch_bot(main_bot: Bot) :
    global bot
    bot = main_bot

# constants

C4_CHANNEL_ID = 1072461314418548736
GAMES_CHANNEL_ID = 1075844926237061180

# discord player functions :

class Ifunc:

    def __init__(self, channel):
        self.channel = channel

    async def __call__(self, name):

        def check(msg):
            return msg.channel == self.channel and msg.author.mention == name

        message: discord.Message = await bot.wait_for("message", check=check)
        return message.content

class Ofunc:

    def __init__(self, channel):
        self.channel = channel

    async def __call__(self, output: io.StringIO):
        await self.channel.send(output)

# main command :

async def command_(admin_role: discord.Role, ctx: Context, game_name: str, action: str, *args: str) :

    match action:

        case "help" :
            await ctx.channel.send(embed=embed_help("p4_help.txt"))

        case "participants":
            # if ctx.channel != bot.get_channel(C4_CHANNEL_ID):
            #     return
            embed = discord.Embed(title="Connect 4 tournament participants")
            embed.description = '\n'.join(f"<@{file.stem}>" for file in AI_DIR.iterdir())
            await ctx.channel.send(embed=embed)

        case "play":

            parser = argparse.ArgumentParser()
            parser.add_argument("users", nargs="*")
            parser.add_argument("-d", "--discord", nargs=1, action="append")
            parsed_args, remaining_args = parser.parse_known_args(args)

            # if ctx.guild and not (ctx.channel == bot.get_channel(GAMES_CHANNEL_ID) and public) :
            #     await ctx.send(f"You need to send this as a DM or in <#{GAMES_CHANNEL_ID}> with the flag `public`.")
            #     return


            users = parsed_args.users

            ai_files = []

            pattern = re.compile(r"^\<\@[0-9]{18}\>$")
            for user in users:
                if pattern.match(user):
                    user_id = user[2:-1]
                    for ai_file in AI_DIR.glob(f"{user_id}.*"):
                        ai_files.append(str(ai_file))
                        break
                    else:
                        await ctx.channel.send(f"{user} has not submitted any AI :cry:")
                        return
                else:
                    await ctx.channel.send(f"{user} is not a valid user")
                    return

            if parsed_args.discord:
                for discord_users in parsed_args.discord:
                    discord_user = discord_users[0]
                    if pattern.match(discord_user):
                        ai_files.append(discord_user)
                    else:
                        await ctx.channel.send(f"{discord_user} is not a valid user")
                        return
            else:
                remaining_args.append("--silent")

            while len(ai_files) < 2:
                await ctx.channel.send("Not enough players to start a game :grimacing:")
                return

            remaining_args.extend(ai_files)
            remaining_args.append("--emoji")

            ofunc = Ofunc(ctx.channel)
            ifunc = Ifunc(ctx.channel)

            with LOG_FILE.open("w") as file:
                with redirect_stdout(file):
                    playerss, winnerr, errors = await puissance4.puissance4.main(remaining_args, ifunc, ofunc, discord=True)

            await ctx.channel.send(file=discord.File(LOG_FILE))
            LOG_FILE.unlink()

        case "tournament":

            if admin_role not in ctx.author.roles :
                return

            await ctx.channel.send(content="Running Connect 4 tournament ...")

            with LOG_FILE.open("w") as file:
                with redirect_stdout(file):
                    os.chdir("./puissance4")
                    scoreboard = await puissance4.tournoi.main(args)
                    os.chdir("..")

            embed = discord.Embed(title="Connect 4 Tournament results")

            lines = []
            for i, (ai, score) in enumerate(scoreboard) :
                lines.append(f"{i+1}. {bot.get_user(int(ai)).mention}, score : {score}")

            embed.add_field(name="Scoreboard", value='\n'.join(lines), inline=False)
            
            await ctx.send(embed=embed)

            await ctx.send(file=discord.File(LOG_FILE))

            LOG_FILE.unlink()

        
        case "submit":

            if ctx.guild:
                await ctx.channel.send("You need to send this as a DM :wink:")
                return

            attachments = ctx.message.attachments
            if not attachments:
                await ctx.channel.send("Missing attachment :poop:")
                return

            attachment = attachments[0]
            new_ext = attachment.filename.split(".")[-1]
            name = str(ctx.message.author.id)
            new_submission = AI_DIR / f"{name}.{new_ext}"

            if not AI_DIR.is_dir():
                AI_DIR.mkdir()

            for ai_file in AI_DIR.glob(f"{name}.*"):
                await ctx.channel.send("Your previous submission will be replaced")
                ai_file.replace(new_submission)
                break
            
            with new_submission.open("w") as file:
                file.write(get(attachment.url).text)

            await ctx.channel.send("AI submitted ! <:feelsgood:737960024390762568>")
        
        case "invite":

            if admin_role not in ctx.author.roles:
                return
            
            user_ids = {int(file.stem) for file in AI_DIR.iterdir()}
            guild_users = {user.id for user in ctx.guild.members}
            missing_users = user_ids.difference(guild_users)

            if missing_users:
                for user_id in missing_users:
                    user = bot.get_user(user_id)
                    await user.create_dm().send(f"Please join our server to take part in the connect4 AI tournament : {ctx.channel.create_invite(max_uses=1)}")
                    await ctx.send(f"Sent invite to {user.mention}")
            else:
                await ctx.send(f"No missing participants on the server :thumbsup:")

        case _:
            await ctx.channel.send("Unknown command")

