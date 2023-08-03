from logging import getLogger

import discord.ext.commands as cmds

from main import CustomBot


logger = getLogger(__name__)

class ErrorHandler(cmds.Cog, name="Errors"):
    """Handles the errors globally across cmds"""

    emote = ":triangular_flag_on_post:"

    def __init__(self, bot: CustomBot):
        self.bot = bot

    @cmds.Cog.listener()
    async def on_command_error(self, ctx: cmds.Context, error: cmds.CommandError):
        """
        Send a message describing the error to discord
        """
        try:
            raise error
        except cmds.ConversionError as d_error:
            await ctx.send(f"{self.emote} {d_error}")
        except cmds.MissingRequiredArgument as d_error:
            assert ctx.command
            await ctx.send(f"{self.emote} Missing argument: `{ctx.command} <{'> <'.join(ctx.command.clean_params)}>`")
        except cmds.MissingRequiredAttachment as d_error:
            await ctx.send(f"{self.emote} Missing required attachement")
        # UserInputError -> BadArgument
        except cmds.MemberNotFound or cmds.UserNotFound as d_error:
            await ctx.send(f"{self.emote} User `{str(d_error).split(' ')[1][1:-1]}` not found")
        # UserInputError -> BadUnionArgument | BadLiteralArgument | ArgumentParsingError
        except cmds.BadArgument or cmds.BadUnionArgument or cmds.BadLiteralArgument or cmds.ArgumentParsingError as d_error:
            await ctx.send(f"{self.emote} {d_error}")
        # CommandNotFound
        except cmds.CommandNotFound as d_error:
            await ctx.send(f"{self.emote} Command `{str(d_error).split(' ')[1][1:-1]}` not found")
        # CheckFailure
        except cmds.PrivateMessageOnly:
            await ctx.send(f"{self.emote} This command can only be used in DM")
        except cmds.NoPrivateMessage:
            await ctx.send(f"{self.emote} This is not working as excpected")
        except cmds.NotOwner:
            await ctx.send(f"{self.emote} You must own this bot to run this command")
        except cmds.MissingPermissions as d_error:
            await ctx.send(f"{self.emote} Your need the following permissions: `{'` `'.join(d_error.missing_permissions)}`.")
        except cmds.BotMissingPermissions as d_error:
            if not "send_messages" in d_error.missing_permissions:
                await ctx.send(f"{self.emote} The bot require the following permissions: `{'` `'.join(d_error.missing_permissions)}`.")
        except cmds.CheckAnyFailure or cmds.MissingRole or cmds.BotMissingRole or cmds.MissingAnyRole or cmds.BotMissingAnyRole as d_error:
            await ctx.send(f"{self.emote} {d_error}")
        except cmds.NSFWChannelRequired:
            await ctx.send(f"{self.emote} This command require an NSFW channel")
        except cmds.CheckFailure as d_error:
            await ctx.send(f"{self.emote} {d_error}")
        # DisabledCommand
        except cmds.DisabledCommand:
            await ctx.send(f"{self.emote} Sorry, this command is disabled")
        # CommandInvokeError
        except cmds.CommandInvokeError as d_error:
            await ctx.send(f"{self.emote} Error during command execution, report to an admin")
            raise d_error
        # CommandOnCooldown
        except cmds.CommandOnCooldown as d_error:
            await ctx.send(f"{self.emote} Command is on cooldown, wait `{str(d_error).split(' ')[7]}` !")
        # MaxConcurrencyReached
        except cmds.MaxConcurrencyReached as d_error:
            await ctx.send(f"{self.emote} Max concurrency reached. Maximum number of concurrent invokers allowed: `{d_error.number}`, per `{d_error.per}`.")


async def setup(bot: CustomBot):
    await bot.add_cog(ErrorHandler(bot))
