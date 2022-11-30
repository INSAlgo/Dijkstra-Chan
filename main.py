import discord
import asyncio
from argparse import ArgumentParser
from datetime import datetime, timedelta

import re
import heapq

from codeforces_client import get_fut_cont_message, get_fut_cont_reminders
from reminder import Reminder


intents = discord.Intents.all()
client = discord.Client(intents=intents)

reminders: list[Reminder] = []


def update_reminders() :
    global reminders
    reminders = []

    err_code, CF_cont_reminders = get_fut_cont_reminders()
    if err_code == 1 :
        print(CF_cont_reminders)

    reminders += CF_cont_reminders

    heapq.heapify(reminders)


async def wait_until(time: datetime) :
    await asyncio.sleep((time - datetime.now()).total_seconds())
    return


@client.event
async def on_ready():
    global reminders

    print(f"We have logged in as {client.user}")
    channel = discord.utils.get(client.get_all_channels(), name="annonces-automatiques")
    update_reminders()
    # print(*reminders)
    
    while reminders :
        next_rem = heapq.heappop(reminders)
        await wait_until(next_rem.time)
        await channel.send(next_rem.msg())


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return

    if message.content.startswith('hi') :
        await message.channel.send('Hello!')

    # Command to get N contests to come :
    elif re.fullmatch("^CodeForces rounds( [0-9]+)?$", message.content) is not None :

        # Parsing the number of contests wanted :
        if message.content[-1].isnumeric() :
            nb = int(message.content.split(' ')[-1])
        else :
            nb = 0

        await message.channel.send(get_fut_cont_message(nb))


if __name__ == "__main__" :

    parser = ArgumentParser(description="")

    parser.add_argument(
        '-t', '--token',
        help="The file to read the token from, or the token itself if -nf.",
        action="store",
        default="token",
        required=False
    )

    parser.add_argument(
        '-nf', '--is_not_file',
        help="If given, reads the file given in -t, else takes -t as the token.",
        action="store_true",
        required=False
    )

    args = parser.parse_args()

    if args.is_not_file :
        token = args.token
    
    else :
        File = open(args.token)
        token = File.readline().strip('\n')
        File.close()

    client.run(token)