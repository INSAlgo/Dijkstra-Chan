from cmath import exp
from os import remove
from requests import get

import discord
import discord.ext.commands as cmds

import matplotlib.pyplot as plt

from modules.geom.check import check
from modules.geom.read import draw_submission

from utils.checks import *
from utils.ids import *

from main import CustomBot


class Geometry(cmds.Cog) :
    """
    Commands related to computational geometry.
    """

    def __init__(self, bot: CustomBot) -> None :
        self.bot = bot
        self.nb_pts_max = 1000000
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
        A bunch of usefull modules for lessons on computational geometry
        (i.e. : convex hulls and fractals)
        """

        if ctx.invoked_subcommand is None:
            raise commands.BadArgument("Invalid subcommand. Use `help geom` for details")

    @geom.command()
    async def CH(self, ctx: cmds.Context, exercise: str = None) :
        return
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
        remove("temp.png")
    
    @geom.command()
    async def IFS(self, ctx: commands.Context, nb_iter: int, *values: float) :
        N = nb_iter

        r = []
        theta = []
        x = []
        y = []

        if len(values) % 4 != 0 or len(values) == 0:
            await ctx.channel.send("Format de l'IFS invalide :poop:")
            return

        for val in values:
            for c in val:
                if c not in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.', '-']:
                    await ctx.channel.send("Format de l\'IFS invalide :poop:")
                    return

        n = len(values) // 4

        if N < 1:
            await ctx.channel.send('Format de l\'IFS invalide :poop:')
            return

        if n ** N > self.nb_pts_max:
            N = self.nb_pts_max // n
            await ctx.channel.send(
                "Désolé j'ai pas une RAM infinie :exploding_head:\n"
                f"le nombre d'itérations a été réduit à {N}"
            )
        
        for i in range(n):
            r.append(float(values[4 * i + 1]))
            theta.append(float(values[4 * i + 2]))
            x.append(float(values[4 * i + 3]))
            y.append(float(values[4 * i + 4]))

        S = {0}
        for it in range(N):
            tmp = set()
            for z in S:
                for i in range(n):
                    tmp.add(z * r[i] * exp(1j * theta[i]) + x[i] + 1j * y[i])
            S = tmp

        X = [z.real for z in S]
        Y = [z.imag for z in S]
        plt.plot(X, Y, 'k,')

        plt.axis('equal')
        plt.savefig("foo.png")
        await ctx.channel.send(file=discord.File("foo.png"))
        plt.clf()
        remove("foo.png")
    
    @geom.command()
    async def IFS2(self, ctx: commands.Context, nb_iter: int, *values: float) :
        N = nb_iter

        A11 = []
        A12 = []
        A21 = []
        A22 = []
        V1 = []
        V2 = []

        if len(values) % 6 != 0 or len(values) == 0:
            await ctx.channel.send('Format de l\'IFS invalide :poop:')
            return

        for val in values:
            for c in val:
                if c not in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.', '-']:
                    await ctx.channel.send('Format de l\'IFS invalide :poop:')
                    return

        n = len(values) // 6

        if N < 1:
            await ctx.channel.send('Format de l\'IFS invalide :poop:')
            return

        if n ** N > self.nb_pts_max:
            N = self.nb_pts_max // n
            await ctx.channel.send(
                "Désolé j'ai pas une RAM infinie :exploding_head:\n"
                f"le nombre d'itérations a été réduit à {N}"
            )

        for i in range(n):
            A11.append(float(values[6 * i + 1]))
            A12.append(float(values[6 * i + 2]))
            A21.append(float(values[6 * i + 3]))
            A22.append(float(values[6 * i + 4]))
            V1.append(float(values[6 * i + 5]))
            V2.append(float(values[6 * i + 6]))

        S = {0}
        for _ in range(N):
            tmp = set()
            for z in S:
                for i in range(n):
                    a = z.real
                    b = z.imag
                    x = A11[i] * a + A12[i] * b + V1[i]
                    y = A21[i] * a + A22[i] * b + V2[i]
                    tmp.add(x + 1j * y)
            S = tmp

        X = [z.real for z in S]
        Y = [z.imag for z in S]
        plt.plot(X, Y, 'k,')

        plt.axis('equal')
        plt.savefig('foo.png')
        await ctx.channel.send(file=discord.File('foo.png'))
        plt.clf()
        remove("foo.png")

async def setup(bot: CustomBot):
    await bot.add_cog(Geometry(bot))
