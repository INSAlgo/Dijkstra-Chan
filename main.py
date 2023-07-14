import asyncio
import logging
import logging.handlers
import os
import discord
import typing

from discord.ext import commands
import pathlib
from utils.help import CustomHelp
from utils import ids

logger = logging.getLogger(__name__)

# Good practices from discord example repository:
# https://github.com/Rapptz/discord.py/blob/v2.3.1/examples/advanced_startup.py

class CustomBot(commands.Bot):

    def __init__(self, *args, **kwargs):
        super().__init__(
                intents=discord.Intents.all(),
                command_prefix="!",
                help_command=CustomHelp(),
                *args,
                **kwargs)
        self.debug_channel: discord.TextChannel

    async def setup_hook(self):

        cog_dir = pathlib.Path("cogs")

        for extension in cog_dir.iterdir():
            if extension.is_file():
                await self.load_extension(f"{cog_dir}.{extension.stem}")
                logger.info(f"extension {extension.stem} loaded")

    async def on_ready(self):
        self.insalgo = typing.cast(discord.Guild, self.get_guild(ids.INSALGO))
        self.debug_channel = typing.cast(discord.TextChannel, self.get_channel(ids.DEBUG))
        await self.debug_channel.send("Up")
        logger.info("bot up")

    async def close(self):
        await self.debug_channel.send("Down")
        await super().close()


async def main():

    # Terminal logger
    logging.basicConfig(format="[%(levelname)s] %(name)s: %(message)s", level=logging.INFO)

    # File logger
    handler = logging.handlers.RotatingFileHandler(filename="bot.log")
    date_format = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', date_format, style='{')
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)

    async with CustomBot() as bot:
        await bot.start(os.getenv('TOKEN', ''))

if __name__ == "__main__":
    asyncio.run(main())
