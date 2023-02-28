from requests import get

import discord
from discord.ext.commands import Bot, Context, command

from bot import bot

from utils.embeding import embed_help
from extensions.geom.check import check
from extensions.geom.read import draw_submission

# Command function :

@command()

async def geom(ctx: Context, course: str = "", *args: str) :
    courses = {"CH"}
    n_args = len(args)
    
    if not bot.check_perm(ctx, ["commands"]) :
        return

    if course not in courses :
        await ctx.channel.send(f"No command named '{course}'. Available commands are : {', '.join(courses)}.")

    if course == "CH" :
        if n_args == 0 :
            await ctx.channel.send("Type of input to specify : points, polygon or help")
            return
        if n_args > 1 :
            await ctx.channel.send("Only one argument required.")
        
        type_ = args[0]
        if type_ == "help" :
            await ctx.channel.send(embed=embed_help("CH_help.txt"))
            return
        if type_ not in {"points", "polygon"} :
            await ctx.channel.send(f"Type of input cannot be '{type_}'. Available types are 'points' and 'polygon'.")
            return

        files = ctx.message.attachments
        if not files:
            await ctx.channel.send("Missing attachment. :poop:")
            return
        attached_file_url = files[0].url
        raw_submission = get(attached_file_url).text

        err_code, res = draw_submission(raw_submission, type_)

        if err_code > 1 :
            await ctx.channel.send(res)
            return
        
        message = check(*res, type_)
        await ctx.channel.send(message, file=discord.File("temp.png"))
        return


# Required setup :

async def setup(bot: Bot) :
    bot.add_command(geom)