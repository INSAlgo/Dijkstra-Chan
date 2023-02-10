import os
from requests import get

import discord
from discord.ext.commands import Context, Bot

from functions.embeding import embed_help
from puissance4.puissance4 import User, AI, game, fallHeight

from numpy import transpose

if not os.path.exists("puissance4/ai") :
    os.mkdir("puissance4/ai")

AIs = {}

for file in os.listdir("puissance4/ai/") :
    name = '.'.join(file.split('.')[:-1])
    ext = file.split('.')[-1]
    if set(c for c in name).issubset({str(i) for i in range(10)}) :
        AIs[name] = ext

numbers = [":zero:", ":one:", ":two:", ":three:", ":four:", ":five:", ":six:", ":seven:", ":eight:", ":nine:", ":keycap_ten:"]

# bot client from main script
bot: Bot

def fetch_bot(main_bot: Bot) :
    global bot
    bot = main_bot


# discord player functions :

def draw_board(board: list[list[int]]) -> list[list[str]] :
    help_line = ' '.join(numbers[:len(board[0])])
    emoji_board = [help_line]
    for line in board :
        emoji_line = []
        for cell in line :
            if cell == 1 :
                emoji = ":red_circle:"
            elif cell == 2 :
                emoji = ":yellow_circle:"
            else :
                emoji = ":black_large_square:"
            emoji_line.append(emoji)
        emoji_board.append(' '.join(emoji_line))
    emoji_board.append(help_line)
    return '\n'.join(emoji_board[::-1])

async def tell_move(move: int, channel: discord.TextChannel) :
    await channel.send(f"Opponent played on column {move}.")

async def ask_move(board: list[list[int]], user: discord.User, channel: discord.TextChannel) :
    
    await channel.send(draw_board(transpose(board)))
    await channel.send("Your move (type `stop` to forfait) :")

    while True :
        resp: discord.Message = await bot.wait_for("message", check=lambda m: m.channel == channel)
        move_txt = resp.content
        if move_txt.lower() == "stop" :
            await channel.send("Okie Dokie !")
            return "stop"
        if move_txt in {str(i) for i in range(len(board))} :
            return move_txt

async def command_(ctx: Context, *args: str) :
    n_args = len(args)

    if n_args == 0 :
        ctx.channel.send("Missing argument")
        return
    
    if args[0] == "help" :
        await ctx.channel.send(embed=embed_help("p4_help.txt"))
        return
    
    if args[0] == "submit" :

        if ctx.guild :
            await ctx.channel.send("You need to send this as a DM :wink:")
            return

        files = ctx.message.attachments
        if not files:
            await ctx.channel.send("Missing attachment. :poop:")
            return
        attached_file_url = files[0].url
        raw_submission = get(attached_file_url).text

        ext = files[0].filename.split('.')[-1]
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
            
        else :
            AIs[name] = ext
            
        if replace :
            File = open(f"puissance4/ai/{name}.{ext}", 'w')
            File.write(raw_submission)
            File.close()

            await ctx.channel.send("AI submitted ! <:feelsgood:737960024390762568>")
        
        else :
            await ctx.channel.send("Okie Dokie !")

        return

    if args[0] == "test" :
        name = str(ctx.message.author.id)

        if name not in AIs.keys() :
            await ctx.channel.send("You don't have an AI! Upload one by messaging me `!p4 submit`.")
            return

        dm = await ctx.message.author.create_dm()

        ext = AIs[name]
        p1 = AI(f"puissance4/ai/{name}.{ext}")
        if "self" in args :
            p2 = User(ask_move, ctx.message.author, dm)
            if "first" in args :
                p1, p2 = p2, p1
        
        else :
            p2 = AI(f"puissance4/ai/{name}.{ext}")
        
        _, _, logs = await game([p1, p2], 7, 6, verbose=False, discord=True)

        File = open("logs", 'w', encoding='utf-8')
        File.write('\n'.join(logs))
        File.close()

        await dm.send(content="logs :", file=discord.File("logs"))
        return