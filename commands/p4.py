import os
from requests import get

import discord
from discord.ext.commands import Context, Bot

from classes.p4Game import P4Game, Player
from functions.embeding import embed_help
from puissance4.puissance4 import User, AI, game, fallHeight

from numpy import transpose

# Connect 4 games setup :
if not os.path.exists("puissance4/ai") :
    os.mkdir("puissance4/ai")

AIs = {}

for file in os.listdir("puissance4/ai/") :
    name = '.'.join(file.split('.')[:-1])
    ext = file.split('.')[-1]
    if set(c for c in name).issubset({str(i) for i in range(10)}) :
        AIs[name] = ext

games: list[P4Game] = []

# bot client from main script
bot: Bot

def fetch_bot(main_bot: Bot) :
    global bot
    bot = main_bot


# discord player functions :

async def tell_move(game_id: int, player: int, move: int, receiver: int) :
    await games[game_id].tell_move(move, player, receiver)

async def ask_move(game_id: int, player: int) :
    return await games[game_id].ask_move(player, bot)


# main command :

async def command_(ctx: Context, *args: str) :
    n_args = len(args)

    if n_args == 0 :
        ctx.channel.send("Missing argument")
        return
    
    if args[0] == "help" :
        await ctx.channel.send(embed=embed_help("p4_help.txt"))
        return
    
    elif args[0] == "get" :
        if ctx.channel != bot.get_channel(1072461314418548736) :
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
        name = str(ctx.message.author.id)

        replace = True

        if not os.path.exists("puissance4/ai") :
            os.mkdir("puissance4/ai")

        if name in AIs.keys() :
            await ctx.channel.send("You already have a submission, do you want to replace it? (Y/N)")

            while True :
                resp: discord.Message = await bot.wait_for("message", check=lambda m: m.channel == ctx.channel)
                if resp.content.upper()[0] == "Y" :
                    replace = True
                    break
                elif resp.content.upper()[0] == "N" :
                    replace = False
                    break
            
            if replace :
                os.remove(f"puissance4/ai/{name}.{AIs[name]}")
            
        if replace :
            File = open(f"puissance4/ai/{name}.{new_ext}", 'w')
            File.write(raw_submission)
            File.close()

            AIs[name] = new_ext

            await ctx.channel.send("AI submitted ! <:feelsgood:737960024390762568>")
        
        else :
            await ctx.channel.send("Okie Dokie !")

        return

    elif args[0] == "test" :
        name = str(ctx.message.author.id)

        if name not in AIs.keys() :
            await ctx.channel.send("You don't have an AI! Upload one by messaging me `!p4 submit`.")
            return

        dm = await ctx.message.author.create_dm()

        game_id = len(games)

        ext = AIs[name]
        p1 = AI(f"puissance4/ai/{name}.{ext}")
        players = [Player("AI", int(name), None)]
        if "self" in args :
            p2 = User(ask_move, tell_move, game_id)
            players.append(Player("User", int(name), dm))
            if "first" in args :
                p1, p2 = p2, p1
                players.reverse()
        
        else :
            p2 = AI(f"puissance4/ai/{name}.{ext}")
            players.append(Player("AI", int(name), None))
        
        game_obj = P4Game(game_id, 2, 7, 6, players)
        games.append(game_obj)
        winner, errors, logs = await game([p1, p2], 7, 6, verbose=False, discord=True)

        winner: Player = players[winner.no-1]
        await game_obj.send_results(f"{winner.get_name()} won!")

        File = open("logs", 'w', encoding='utf-8')
        File.write('\n'.join(logs))
        File.close()

        await dm.send(content="logs :", file=discord.File("logs"))
        return