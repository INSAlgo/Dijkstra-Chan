import os
from requests import get

import discord
from discord.ext.commands import Context, Bot

from functions.embeding import embed_help

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
        name = ctx.message.author.name + '.' + ext

        replace = True

        if not os.path.exists("puissance4/ai") :
            os.mkdir("puissance4/ai")

        if os.path.exists(f"puissance4/ai/{name}") :
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
            File = open(f"puissance4/ai/{name}", 'w')
            File.write(raw_submission)
            File.close()

            await ctx.channel.send("AI submitted ! <:feelsgood:737960024390762568>")
        
        else :
            await ctx.channel.send("Okie Dokie !")