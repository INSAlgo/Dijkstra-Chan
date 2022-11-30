import discord
import asyncio
from argparse import ArgumentParser
from datetime import datetime, timedelta

import re
import heapq

from codeforces_client import get_fut_cont_message, get_fut_cont_reminders
from event import msg_to_event
from reminder import Reminder


intents = discord.Intents.all()
client = discord.Client(intents=intents)

reminders: list[Reminder] = []
remind_instance = 0


def update_reminders() :
    global reminders
    reminders = []

    err_code, CF_cont_reminders = get_fut_cont_reminders(test=True)
    if err_code == 1 :
        print(CF_cont_reminders)

    reminders += CF_cont_reminders

    heapq.heapify(reminders)


async def wait_until(time: datetime) :
    if (time - datetime.now()).total_seconds() < 0 :
        return 1
    await asyncio.sleep((time - datetime.now()).total_seconds())
    return 0


async def remind(instance: int) :
    global reminders
    channel = discord.utils.get(client.get_all_channels(), name="annonces-automatiques")

    while reminders :
        next_rem = reminders[0]
        err_code = await wait_until(next_rem.time)

        if remind_instance != instance :
            return

        if err_code == 0 :
            await channel.send(next_rem.msg())
        heapq.heappop(reminders)


@client.event
async def on_ready() :
    update_reminders()
    remind(0)


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
    
    # Command to add an event to the queue of reminders :
    elif message.content.startswith("add event reminders") :
        global remind_instance
        event = msg_to_event(message.content)

        if event is None :
            await message.channel.send("please format the date as YYYY/MM/DD HH:MM")
        
        else :
            heapq.heappush(reminders, Reminder(event, "5min"))
            heapq.heappush(reminders, Reminder(event, "hour"))
            heapq.heappush(reminders, Reminder(event, "day"))
            remind_instance += 1
            remind(remind_instance)
            await message.channel.send(f"Reminders for {event.name} have been succesfully added to the queue!")


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