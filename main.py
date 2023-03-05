import asyncio
import logging
import logging.handlers
import os
import discord


from discord.ext import commands
import pathlib

from discord.ext.commands.context import is_cog
logger = logging.getLogger(__name__)

COG_DIR = pathlib.Path("cogs")

class CustomBot(commands.Bot):

    def __init__(self, *args, **kwargs):
        super().__init__(intents=discord.Intents.all(), command_prefix="!", *args, **kwargs)

    async def setup_hook(self):

        for extension in COG_DIR.iterdir():
            if extension.is_file():
                await self.load_extension(f"{COG_DIR}.{extension.stem}")

    async def on_ready(self):

        self.debug_channel = self.get_channel(1048584804301537310)

        await self.debug_channel.send("Up")
        logger.info("bot up")

async def main():

    # Terminal logger
    logging.basicConfig(format="[%(levelname)s] %(name)s: %(message)s", level=logging.INFO)

    # File logger
    handler = logging.handlers.RotatingFileHandler(
        filename="bot.log",
        maxBytes=1 * 1024 * 1024,  # 1 MiB
        backupCount=2,  # Rotate through 2 files
    )
    date_format = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', date_format, style='{')
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)

    async with CustomBot() as bot:
        await bot.start(os.getenv('TOKEN', ''))


if __name__ == "__main__":
    asyncio.run(main())
