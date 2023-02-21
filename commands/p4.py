import os
from requests import get
import re

import discord
from discord.ext.commands import Context, Bot

from classes.p4Game import P4Game, Player
from functions.embeding import embed_help
from puissance4.puissance4 import User, AI, game
from puissance4.tournoi import tournament

# Connect 4 games setup :
if not os.path.exists("puissance4/ai") :
    os.mkdir("puissance4/ai")

AIs = {}

for file in os.listdir("puissance4/ai/") :
    name = '.'.join(file.split('.')[:-1])
    ext = file.split('.')[-1]
    if set(c for c in name).issubset({str(i) for i in range(10)}) :
        AIs[int(name)] = ext

games: list[P4Game] = []

# bot client from main script
bot: Bot

def fetch_bot(main_bot: Bot) :
    global bot
    bot = main_bot

# constants

c4_channel_id = 1072461314418548736
games_channel_id = 1075844926237061180

# discord player functions :

async def tell_move(game_id: int, player: int, move: int, receiver: int) :
    await games[game_id].tell_move(move, player, receiver)

async def ask_move(game_id: int, player: int) :
    return await games[game_id].ask_move(player, bot)


# main command :

async def command_(admin_role: discord.Role, ctx: Context, *args: str) :
    n_args = len(args)

    if n_args == 0 :
        ctx.channel.send("Missing argument")
        return
    
    if args[0] == "help" :
        await ctx.channel.send(embed=embed_help("p4_help.txt"))
        return
    
    elif args[0] == "get" :
        if ctx.channel != bot.get_channel(c4_channel_id) :
            return
        embed = discord.Embed(title="Connect 4 tournament participants")
        desc = [f"<@{id_}>" for id_ in AIs.keys()]
        embed.description = '\n'.join(desc)
        await ctx.channel.send(embed=embed)
    
    elif args[0] == "submit" :

        if ctx.guild :
            await ctx.channel.send("You need to send this as a DM :wink:")
            return

        files = ctx.message.attachments
        if not files:
            await ctx.channel.send("Missing attachment. :poop:")
            return
        attached_file_url = files[0].url
        raw_submission = get(attached_file_url).text

        new_ext = files[0].filename.split('.')[-1]
        name = ctx.message.author.id

        replace = True

        if not os.path.exists("puissance4/ai") :
            os.mkdir("puissance4/ai")

        if name in AIs.keys() :
            await ctx.channel.send("Your old submission will be replaced with this one.")
            os.remove(f"puissance4/ai/{name}.{AIs[name]}")
            
        File = open(f"puissance4/ai/{name}.{new_ext}", 'w')
        File.write(raw_submission)
        File.close()

        AIs[name] = new_ext

        await ctx.channel.send("AI submitted ! <:feelsgood:737960024390762568>")

        return

    elif args[0] == "test" :
        if ctx.guild and not (ctx.channel == bot.get_channel(games_channel_id) and "public" in args) :
            ctx.send(f"You need to send this as a DM or in <#{games_channel_id}> with the flag `public`.")
            return
        
        name = ctx.message.author.id

        if name not in AIs.keys() :
            await ctx.channel.send("You don't have an AI! Upload one by messaging me `!p4 submit`.")
            return

        dm = await ctx.message.author.create_dm()

        game_id = len(games)

        ext = AIs[name]
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

        File = open("logs", 'w', encoding='utf-8')
        File.write('\n'.join(logs))
        File.close()

        await dm.send(content="logs :", file=discord.File("logs"))
        return

    elif args[0] == "challenge" :
        public = "public" in args

        if ctx.guild and not (ctx.channel == bot.get_channel(games_channel_id) and public) :
            await ctx.send(f"You need to send this as a DM or in <#{games_channel_id}> with the flag `public`.")
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
            if p1_id not in AIs :
                await ctx.send("You don't have an AI! Upload one by messaging me `!p4 submit`.")
            game_players.append(AI(f"puissance4/ai/{p1_id}.{AIs[p1_id]}"))
            local_players.append(Player("AI", p1_id, None))
        else :
            game_players.append(User(ask_move, tell_move, game_id))
            local_players.append(Player("User", p1_id, dm1))

        if type2 == "AI" :
            if p2_id not in AIs :
                await ctx.send("This user has never submited any AI")
            game_players.append(AI(f"puissance4/ai/{p2_id}.{AIs[p2_id]}"))
            local_players.append(Player("AI", p2_id, None))
        else :
            game_players.append(User(ask_move, tell_move, game_id))
            local_players.append(Player("User", p2_id, dm2))

        game_obj = P4Game(game_id, 2, 7, 6, local_players)
        games.append(game_obj)
        _, winner, errors, logs = await game(game_players, 7, 6, verbose=False, discord=True)

        winner: Player = local_players[winner.no-1]

        File = open("logs", 'w', encoding='utf-8')
        File.write('\n'.join(logs))
        File.close()

        if public :
            await ctx.send(f"{game_obj.draw_board()}\n{winner.get_name()} won!")
            await ctx.send(content="logs :", file=discord.File("logs"))
        else :
            await game_obj.send_results(f"{winner.get_name()} won!")
            await dm1.send(content="logs :", file=discord.File("logs"))
            await dm2.send(content="logs :", file=discord.File("logs"))

        os.remove("logs")

        return

    elif args[0] == "tournament" :
        if admin_role not in ctx.author.roles :
            return
        
        if len(args) == 1 :
            r = 3
        else :
            r = int(args[1])
        

        embed = discord.Embed(title= "Connect 4 Tournament results")
        lines = []

        os.chdir("./puissance4")
        scoreboard, logs = await tournament(rematches=r)
        os.chdir("..")

        i = 1
        for AI_, score in scoreboard :
            lines.append(f"{i} : <@{int(AI_)}> with a score of {score}")
            i += 1

        embed.add_field(name="Scoreboard :", value='\n'.join(lines), inline=False)
        
        await ctx.send(embed=embed)

        games_log = []

        for players, winner, errors in logs :
            line = " vs. ".join([f"<@{int(p)}>" for p in players]) + " --> "
            if winner is None :
                line += "Draw"
            else :
                line += f"<@{int(winner)}>"
            
            if len(errors) > 0 :
                line += '\n'
                line += '\n'.join(f"error with <@{int(players[p_n-1])}>'s AI : {e}" for p_n, e in errors.items())
            games_log.append(line)
        
        File = open("games", 'w', encoding='utf-8')
        File.write('\n'.join(games_log))
        File.close()

        await ctx.send(content="Games log :", file=discord.File("games"))

        os.remove("games")