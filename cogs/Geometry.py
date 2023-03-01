import os
from requests import get

import discord
import discord.ext.commands as cmds

from utils.IDs import *
from utils.checks import *

from utils.embeding import embed_help
from utils.geom.check import check
from utils.geom.read import draw_submission

# Geometry Cog :

class GeometryCog(cmds.Cog) :
    def __init__(self) -> None :
        self.commands = {"CH": {"points", "polygon"}}
    
    @staticmethod
    async def process_submission(type_: str, ctx: cmds.Context) :
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
        os.remove("temp.png")
    
    @commands.group(pass_context=True)
    @in_channel(COMMANDS, False)
    async def geom(self, ctx: cmds.Context) :
        if ctx.invoked_subcommand is None:
            text = ', '.join(self.commands.keys())
            await ctx.send(f"Invalid course, available courses are : {text}.")

    @geom.command()
    async def help(self, ctx: cmds.Context) :
        await ctx.send("TODO :)")

    @geom.group(pass_context=True)
    async def CH(self, ctx: cmds.Context) :
        if ctx.invoked_subcommand is None:
            text = ', '.join(self.commands["CH"])
            await ctx.send(f"Invalid exercise, available exercises are : {text}.")

    @CH.command()
    async def help(self, ctx: cmds.Context) :
        await ctx.send("TODO :)")
    
    @CH.command()
    async def points(self, ctx: cmds.Context) :
        await self.process_submission("points", ctx)
    
    @CH.command()
    async def polygon(self, ctx: cmds.Context) :
        await self.process_submission("polygon", ctx)