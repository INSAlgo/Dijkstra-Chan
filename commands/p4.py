import os
from requests import get

import discord
from discord.ext.commands import Context, Bot

from functions.embeding import embed_help
from puissance4.puissance4 import User, AI, game

if not os.path.exists("puissance4/ai") :
    os.mkdir("puissance4/ai")

AIs = {}

for file in os.listdir("puissance4/ai/") :
    name = '.'.join(file.split('.')[:-1])
    ext = file.split('.')[-1]
    if set(c for c in name) == {str(i) for i in range(10)} :
        AIs[name] = ext


async def ask_move(board: list[list[int]], user: discord.User, channel: discord.TextChannel) :
    pass

async def command_(bot: Bot, ctx: Context, *args: str) :
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
        name = ctx.message.author.id

        replace = True

        if not os.path.exists("puissance4/ai") :
            os.mkdir("puissance4/ai")

        if name in AIs :
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
        name = ctx.message.author.id
        
        if name not in AIs :
            await ctx.channel.send("You don't have an AI! Upload one by messaging me `!p4 submit`.")
            return

        dm = await ctx.message.author.create_dm()

        ext = AIs[name]
        if "self" in args :
            p1 = AI(f"puissance4/ai/{name}.{ext}")
            p2 = User(ask_move, ctx.message.author, dm)
            if "first" in args :
                p1, p2 = p2, p1
        
        _, _, logs = game([p1, p2], 7, 6, verbose=True, discord=True)

        File = open("logs", 'w')
        File.write(logs)
        File.close()

        await dm.send(content="logs :", file=discord.File("logs"))
        return

