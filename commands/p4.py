import argparse
from contextlib import redirect_stdout
import os
import pathlib
from matplotlib.rcsetup import validate_any
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

async def tell_move(game_id: int, player: int, move: int, receiver: int) :
    await games[game_id].tell_move(move, player, receiver)

async def ask_move(game_id: int, player: int) :
    return await games[game_id].ask_move(player, bot)


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
            parser.add_argument("--public", action="store_true")
            parsed_args, remaining_args = parser.parse_known_args(args)

            public = parsed_args.public

            # if ctx.guild and not (ctx.channel == bot.get_channel(GAMES_CHANNEL_ID) and public) :
            #     await ctx.send(f"You need to send this as a DM or in <#{GAMES_CHANNEL_ID}> with the flag `public`.")
            #     return

            pattern = re.compile(r"^\<\@[0-9]{18}\>$")

            users = parsed_args.users
            while len(users) < 2:
                users.append(ctx.author.mention)
            ai_files = []

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

            remaining_args.extend(ai_files)

            with LOG_FILE.open("w") as file:
                with redirect_stdout(file):
                    playerss, winnerr, errors = await puissance4.puissance4.main(remaining_args)

            line = []
            if winnerr:
                line.append(f"{bot.get_user(int(str(winnerr))).mention} won !")
            else:
                line.append("Draw")
            if errors:
                for player, error in errors.items():
                    line.append(f"({bot.get_user(int(str(player))).mention} : {error})")

            await ctx.channel.send("\n".join(line), file=discord.File(LOG_FILE))


        case "tournament":

            if admin_role not in ctx.author.roles :
                return

            await ctx.channel.send(content="Running connect 4 tournament ...")

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
            embed.add_field(name="Games log", value="", inline=True)
            
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

    return

    if args[0] == "test" :

        if ctx.guild and not (ctx.channel == bot.get_channel(GAMES_CHANNEL_ID) and "public" in args) :
            await ctx.send(f"You need to send this as a DM or in <#{GAMES_CHANNEL_ID}> with the flag `public`.")
            return
        
        name = ctx.message.author.id

        if name not in ais.keys() :
            await ctx.channel.send("You don't have an AI! Upload one by messaging me `!p4 submit`.")
            return

        if "public" in args :
            dm = ctx.channel
        else :
            dm = await ctx.message.author.create_dm()

        game_id = len(games)

        ext = ais[name]
        p1 = AI(f"puissance4/ai/{name}.{ext}")
        players = [Player("AI", name, None)]
        if "self" in args :
            p2 = User(ask_move, tell_move, game_id)
            players.append(Player("User", name, dm))
            if "first" in args :
                p1, p2 = p2, p1
                players.reverse()
        
        else :
            p2 = AI(f"puissance4/ai/{name}.{ext}")
            players.append(Player("AI", name, None))
        
        game_obj = P4Game(game_id, 2, 7, 6, players)
        games.append(game_obj)
        _, winner, errors, logs = await game([p1, p2], 7, 6, verbose=False, discord=True)

        winner: Player = players[winner.no-1]
        await game_obj.send_results(f"{winner.get_name()} won!")

        log_file = open("logs", 'w', encoding='utf-8')
        log_file.write('\n'.join(logs))
        log_file.close()

        await dm.send(content="logs :", file=discord.File("logs"))
        return

    elif args[0] == "challenge" :
        public = "public" in args

        if ctx.guild and not (ctx.channel == bot.get_channel(GAMES_CHANNEL_ID) and public) :
            await ctx.send(f"You need to send this as a DM or in <#{GAMES_CHANNEL_ID}> with the flag `public`.")
            return

        if len(args) < 3 :
            ctx.send("not enough args, see `!p4 help` for more information")
            return
        
        p1 = ctx.message.author
        p1_id = p1.id

        if re.match("^\<\@[0-9]{18}\>$", args[1]) is None :
            await ctx.send(f"{args[1]} is not a valid Discord tag/mention.")
            if not ctx.guild :
                await ctx.send(f"You need to use `<@user_id>` to tag someone in DMs.")
            return
        
        p2_id = int(args[1][2:-1])
        p2 = bot.get_user(p2_id)
        if p2 is None :
            await ctx.send(f"User <@{p2_id}> not found.")
            return

        if args[2] not in {"User_User", "User_AI", "AI_User", "AI_AI"} :
            await ctx.send("Invalid game type, see `!p4 help` for more info.")
        type1, type2 = args[2].split('_')

        if public :
            dm1, dm2 = ctx.channel, ctx.channel
        else :
            dm1, dm2 = await p1.create_dm(), await p2.create_dm()
        
        # asking for player2 permission :

        await ctx.channel.send(f"Hey <@{p2_id}>, <@{p1_id}> challenges you to a fight ({type1} vs {type2}), do you accept ? (Y/N, see `!p4 help` for details)")

        for _ in range(10) :
            resp: discord.Message = await bot.wait_for("message", check=lambda m: (m.channel == dm2) and (m.author == p2))
            if resp.content.upper()[0] == "Y" :
                break
            elif resp.content.upper()[0] == "N" :
                dm1.send(f"Connect 4 game challenge to <@{p1_id}> ({type1} vs {type2}) was refused.")
                return
        
        else :
            if public :
                dm1.send(f"Connect 4 game between <@{p1_id}> and <@{p2_id}> ({type1} vs {type2}) was cancelled.")
            else :
                dm1.send(f"Connect 4 game challenge to <@{p2_id}> ({type1} vs {type2}) was cancelled.")
                dm2.send(f"Connect 4 game challenge from <@{p1_id}> ({type1} vs {type2}) was cancelled.")

        game_players = []
        local_players = []
        game_id = len(games)

        if type1 == "AI" :
            if p1_id not in ais :
                await ctx.send("You don't have an AI! Upload one by messaging me `!p4 submit`.")
            game_players.append(AI(f"puissance4/ai/{p1_id}.{ais[p1_id]}"))
            local_players.append(Player("AI", p1_id, None))
        else :
            game_players.append(User(ask_move, tell_move, game_id))
            local_players.append(Player("User", p1_id, dm1))

        if type2 == "AI" :
            if p2_id not in ais :
                await ctx.send("This user has never submited any AI")
            game_players.append(AI(f"puissance4/ai/{p2_id}.{ais[p2_id]}"))
            local_players.append(Player("AI", p2_id, None))
        else :
            game_players.append(User(ask_move, tell_move, game_id))
            local_players.append(Player("User", p2_id, dm2))

        game_obj = P4Game(game_id, 2, 7, 6, local_players)
        games.append(game_obj)
        _, winner, errors, logs = await game(game_players, 7, 6, verbose=False, discord=True)

        if winner is None :
            win_txt = "Draw."
        
        else :
            win_txt: str = local_players[winner.no-1].get_name() + " won!"

        log_file = open("logs", 'w', encoding='utf-8')
        log_file.write('\n'.join(logs))
        log_file.close()

        if public :
            await ctx.send(f"{game_obj.draw_board()}\n{win_txt}")
            await ctx.send(content="logs :", file=discord.File("logs"))
        else :
            await game_obj.send_results(f"{win_txt}")
            await dm1.send(content="logs :", file=discord.File("logs"))
            await dm2.send(content="logs :", file=discord.File("logs"))

        os.remove("logs")

        return
    
