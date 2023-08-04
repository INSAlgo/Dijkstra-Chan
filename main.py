import logging, logging.handlers, typing
from pathlib import Path
from asyncio import run
from requests import post
from os import environ

import discord
import discord.ext.commands as cmds

from utils.help import CustomHelp
from utils.ids import *


logger = logging.getLogger(__name__)

# Good practices from discord example repository:
# https://github.com/Rapptz/discord.py/blob/v2.3.1/examples/advanced_startup.py
class CustomBot(cmds.Bot):

    def __init__(self, *args, **kwargs):
        super().__init__(
                intents=discord.Intents.all(),
                command_prefix="!",
                help_command=CustomHelp(),
                *args,
                **kwargs)
        self.debug_channel: discord.TextChannel

    async def setup_hook(self):

        cog_dir = Path("cogs")

        for extension in cog_dir.iterdir():
            if extension.is_file():
                await self.load_extension(f"{cog_dir}.{extension.stem}")
                logger.info(f"extension {extension.stem} loaded")

    async def on_ready(self):
        self.insalgo = typing.cast(discord.Guild, self.get_guild(INSALGO))
        self.debug_channel = typing.cast(discord.TextChannel, self.get_channel(DEBUG))
        await self.debug_channel.send("Up")
        logger.info("bot up")


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
        await bot.start(environ['DISCORD_TOKEN'])

if __name__ == "__main__":
    try:
        run(main())
    except KeyboardInterrupt as kb_interrupt:
        pass
    
    # Sending a message to confirm shutdown :
    headers = {'Authorization': 'Bot %s' % environ['DISCORD_TOKEN'] }
    post(f"https://discord.com/api/v6/channels/{DEBUG}/messages", headers=headers, json={"content": "Down"})
#hehe