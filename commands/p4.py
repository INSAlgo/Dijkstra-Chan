import argparse
import contextlib
import pathlib
import requests
import re

import discord
from discord.ext.commands import Context, Bot

from functions import embeding, tournoi
from submodules.puissance4 import puissance4

# Constants
GAMES_DIR = pathlib.Path("submodules")
AI_DIR_NAME = "ai"

TOURNAMENT_CHANNEL_ID = 1072461314418548736
GAMES_CHANNEL_ID = 1075844926237061180
DEBUG_CHANNEL_ID = 1048584804301537310

# bot client from main script
bot: Bot
def fetch_bot(main_bot: Bot) :
    global bot
    bot = main_bot


class Game():
    
    def __init__(self, name, directory, cmd, module) -> None:
        self.name = name
        self.directory = directory
        self.cmd = cmd
        self.module = module
        self.game_dir = GAMES_DIR / self.directory
        self.ai_dir = self.game_dir / AI_DIR_NAME
        self.log_file = self.game_dir / "log.txt"

GAMES = {"p4": Game("Connect 4", "puissance4", "p4", puissance4, )}



# discord player functions :

class Ifunc:

    def __init__(self, channel):
        self.channel = channel

    async def __call__(self, name: str):
        def check(msg):
            return msg.channel == self.channel and msg.author.mention == name
        message: discord.Message = await bot.wait_for("message", check=check)
        return message.content

class Ofunc:

    def __init__(self, channel):
        self.channel = channel

    async def __call__(self, output: str):
        await self.channel.send(output)

# main command :

async def command_(admin_role: discord.Role, ctx: Context, game_name: str, action: str, *args: str) :

    tournament_channel = bot.get_channel(TOURNAMENT_CHANNEL_ID)
    game_channel = bot.get_channel(GAMES_CHANNEL_ID)
    debug_channel = bot.get_channel(DEBUG_CHANNEL_ID)
    
    if game_name not in GAMES:
        await ctx.send(f"Unknown game `{game_name}`. Here is what we have for now :\n`"
                               + "`, `".join(GAMES) + "`")
        return

    game = GAMES[game_name]

    match action:

        case "help" :
            await ctx.send(embed=embeding.embed_help(f"{game.cmd}_help.txt"))

        case "participants":
            if ctx.channel not in (tournament_channel, debug_channel):
                await ctx.send(f"Use this command in the {tournament_channel.mention} channel :wink:")
                return
            embed = discord.Embed(title=f"{game.name} tournament participants")
            embed.description = '\n'.join(f"<@{file.stem}>" for file in game.ai_dir.iterdir())
            await ctx.send(embed=embed)

        case "play":

            if ctx.guild and ctx.channel not in (game_channel, debug_channel):
                await ctx.send(f"You need to send this as a DM or in {game_channel.mention}")
                return

            game_args = []
            
            players = []
            pattern = re.compile(r"^\<\@[0-9]{18}\>$")
            ai_only = True
            is_human = False

            for arg in args:
                if arg == "-d" or arg == "--discord":
                    is_human = True
                    continue
                if not arg.startswith("-"):
                    if pattern.match(arg):
                        user = bot.get_user(int(arg[2:-1]))
                        if user:
                            if is_human:
                                players.append(arg)
                                ai_only = False
                            else:
                                for ai_file in game.ai_dir.glob(f"{user.id}.*"):
                                    players.append(str(ai_file))
                                    break
                                else:
                                    await ctx.send(f"{user.mention} has not submitted any AI :cry:")
                            is_human = False
                    else:
                        await ctx.send(f"Invalid argument {arg} :face_with_raised_eyebrow:")

            if len(players) < 2:
                await ctx.send("Not enough players to start a game :grimacing:")
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

            if admin_role not in ctx.author.roles:
                await ctx.send("Admins only can start a tournament")
                return

            with game.log_file.open("w") as file:
                with contextlib.redirect_stdout(file):
                    scoreboard = await tournoi.main(bot, ctx, game, args)
            game.log_file.touch()

            embed = discord.Embed(title=f"{game.name} tournament results")

            lines = []
            for i, (ai, score) in enumerate(scoreboard) :
                lines.append(f"{i+1}. {bot.get_user(int(ai)).mention} score : {score}")

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

            if admin_role not in ctx.author.roles:
                return
            
            user_ids = {int(file.stem) for file in game.ai_dir.iterdir()}
            guild_users = {user.id for user in ctx.guild.members}
            missing_users = user_ids.difference(guild_users)

            if missing_users:
                for user_id in missing_users:
                    ai = bot.get_user(user_id)
                    await ai.create_dm().send(f"Please join our server to take part in the connect4 AI tournament : {ctx.channel.create_invite(max_uses=1)}")
                    await ctx.send(f"Sent invite to {ai.mention}")
            else:
                await ctx.send(f"No missing participants on the server :thumbsup:")

        case _:
            await ctx.send("Unknown command")

