import discord
from discord.ext import commands

class ErrorHandler(commands.Cog):

    emote = ":triangular_flag_on_post:"

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        try:
            raise error
        except commands.ConversionError as d_error:
            await ctx.send(f"{self.emote} {d_error}")
        except commands.MissingRequiredArgument as d_error:
            await ctx.send(f"{self.emote} Missing argument: `{ctx.clean_prefix}{ctx.command} <{'> <'.join(ctx.command.clean_params)}>`")
        except commands.MissingRequiredAttachment as d_error:
            await ctx.send(f"{self.emote} Missing required attachement")
        # UserInputError -> BadArgument
        except commands.MemberNotFound or commands.UserNotFound as d_error:
            await ctx.send(f"{self.emote} User `{str(d_error).split(' ')[1][1:-1]}` not found")
        # UserInputError -> BadUnionArgument | BadLiteralArgument | ArgumentParsingError
        except commands.BadArgument or commands.BadUnionArgument or commands.BadLiteralArgument or commands.ArgumentParsingError as d_error:
            await ctx.send(f"{self.emote} {d_error}")
        # CommandNotFound
        except commands.CommandNotFound as d_error:
            await ctx.send(f"{self.emote} Command `{str(d_error).split(' ')[1][1:-1]}` not found")
        # CheckFailure
        except commands.PrivateMessageOnly:
            await ctx.send(f"{self.emote} This command can only be used in DM")
        except commands.NoPrivateMessage:
            await ctx.send(f"{self.emote} This is not working as excpected")
        except commands.NotOwner:
            await ctx.send(f"{self.emote} You must own this bot to run this command")
        except commands.MissingPermissions as d_error:
            await ctx.send(f"{self.emote} Your need the following permissions: `{'` `'.join(d_error.missing_permissions)}`.")
        except commands.BotMissingPermissions as d_error:
            if not "send_messages" in d_error.missing_permissions:
                await ctx.send(f"{self.emote} The bot require the following permissions: `{'` `'.join(d_error.missing_permissions)}`.")
        except commands.CheckAnyFailure or commands.MissingRole or commands.BotMissingRole or commands.MissingAnyRole or commands.BotMissingAnyRole as d_error:
            await ctx.send(f"{self.emote} {d_error}")
        except commands.NSFWChannelRequired:
            await ctx.send(f"{self.emote} This command require an NSFW channel")
        except commands.CheckFailure as d_error:
            await ctx.send(f"{self.emote} {d_error}")
        # DisabledCommand
        except commands.DisabledCommand:
            await ctx.send(f"{self.emote} Sorry, this command is disabled")
        # CommandInvokeError
        except commands.CommandInvokeError as d_error:
            await ctx.send(f"{self.emote} {d_error.original}")
        # CommandOnCooldown
        except commands.CommandOnCooldown as d_error:
            await ctx.send(f"{self.emote} Command is on cooldown, wait `{str(d_error).split(' ')[7]}` !")
        # MaxConcurrencyReached
        except commands.MaxConcurrencyReached as d_error:
            await ctx.send(f"{self.emote} Max concurrency reached. Maximum number of concurrent invokers allowed: `{d_error.number}`, per `{d_error.per}`.")


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
