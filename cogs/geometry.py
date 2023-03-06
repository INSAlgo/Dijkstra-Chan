import os
from requests import get

import discord
import discord.ext.commands as cmds
from main import CustomBot

from utils.ids import *
from utils.checks import *

from functions.geom.check import check
from functions.geom.read import draw_submission


class Geometry(cmds.Cog) :
    """
    Commands related to computational geometry.
    """

    def __init__(self, bot: CustomBot) -> None :
        self.bot = bot
        self.CH_exos = {"points", "polygon"}
        self.CH_exos_txt = ', '.join(f"`{ex}`" for ex in self.CH_exos)

        self.CH.brief = "Commands for the lesson on Convex Hulls"
        self.CH.help = f"""Commands to check if the output file produced by your algorithm is valid for the exercises on Convex Hull
        Allowed exercises are {self.CH_exos_txt}
        You need to attach the output file of your code to the message"""
        self.CH.help += """
        Your file must be formatted this way :
        - the number of points (an integer)
        - points as '<x> <y>' (in the order if it's a polygon)
        - the number of points of the hull (an integer)
        - points of the hull as '<x> <y>'"""
    
    @commands.group(pass_context=True)
    @in_channel(COMMANDS, force_guild=False)
    async def geom(self, ctx: cmds.Context) :
        """
        A bunch of usefull functions for lessons on computational geometry
        (i.e. : convex hulls and fractals)
        """

        if ctx.invoked_subcommand is None:
            raise commands.BadArgument("Invalid subcommand. Use `!help geom` for details")

    @geom.command()
    async def CH(self, ctx: cmds.Context, exercise: str = None) :

        if exercise not in self.CH_exos :
            message = f"Invalid exercise `{exercise}`, available exercises are : {self.CH_exos_txt}"
            raise commands.BadArgument(message)
        
        files = ctx.message.attachments
        if not files:
            await ctx.channel.send("Missing attachment. :poop:")
            return
        attached_file_url = files[0].url
        raw_submission = get(attached_file_url).text

        err_code, res = draw_submission(raw_submission, exercise)

        if err_code > 1 :
            await ctx.channel.send(res)
            return
        
        message = check(*res, exercise)
        await ctx.channel.send(message, file=discord.File("temp.png"))
        os.remove("temp.png")
    
    @geom.command()
    async def fractal(self, ctx: commands.Context) :
        """
        Commands for the lesson on fractals (WIP).
        """
        await ctx.channel.send("This command is not working yet!")

async def setup(bot):
    await bot.add_cog(Geometry(bot))
