import asyncio
import logging
import logging.handlers
import os
import discord
import requests

from discord.ext import commands
import pathlib
from utils.help import CustomHelp

logger = logging.getLogger(__name__)

class CustomBot(commands.Bot):

    def __init__(self, *args, **kwargs):
        super().__init__(
                intents=discord.Intents.all(),
                command_prefix="!",
                help_command=CustomHelp(),
                *args,
                **kwargs)

    async def setup_hook(self):

        cog_dir = pathlib.Path("cogs")

        for extension in cog_dir.iterdir():
            if extension.is_file():
                await self.load_extension(f"{cog_dir}.{extension.stem}")

    async def on_ready(self):

        self.debug_channel = self.get_channel(1048584804301537310)
        assert isinstance(self.debug_channel, discord.TextChannel)
        await self.debug_channel.send("Up")
        logger.info("bot up")

    async def close(self):
        logger.info("shuting down")
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

    headers = {'Authorization': 'Bot %s' % os.getenv('TOKEN', '')}
    requests.post(f"https://discord.com/api/v6/channels/1048584804301537310/messages", headers=headers, json={"content": "Down"})


if __name__ == "__main__":
    asyncio.run(main())
