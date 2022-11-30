import discord
import asyncio
from argparse import ArgumentParser
from datetime import datetime

import re
from queue import PriorityQueue as PQ

from codeforces_client import get_fut_cont_message, get_fut_cont_events
from event import Event, msg_to_event, save_events, load_events
from reminder import Reminder, generate_queue


intents = discord.Intents.all()
client = discord.Client(intents=intents)
notif_channel: discord.TextChannel = None

events: set[Event] = set()
reminders: PQ[Reminder] = PQ()
cur_rem: asyncio.Task[None] | None = None


async def wait_reminder() :
    global reminders

    time = (reminders.queue[0].time - datetime.now()).total_seconds()
    print("waiting for a reminder...")
    await asyncio.sleep(time)
    await notif_channel.send(reminders.get().msg())

    # Loops to wait for the next reminder
    global cur_rem
    if reminders.empty() :
        cur_rem = None
    else :
        cur_rem = asyncio.ensure_future(wait_reminder())

@client.event
async def on_ready() :
    global events
    events = load_events()
    err_code, CF_contests = get_fut_cont_events()
    if err_code > 0 :
        print(CF_contests)
    else :
        events |= CF_contests
    
    global reminders
    reminders = generate_queue(events)

    global notif_channel
    notif_channel = discord.utils.get(client.get_all_channels(), name="annonces-automatiques")

    global cur_rem
    if cur_rem is not None :
        cur_rem.cancel()
    if reminders.empty() :
        cur_rem = None
    else :
        cur_rem = asyncio.ensure_future(wait_reminder())


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
    
    # Command to add an event :
    elif message.content.startswith("add event") :
        event = msg_to_event(message.content)

        if event is None :
            await message.channel.send("please format the date as YYYY/MM/DD HH:MM")
        
        else :
            global events
            global reminders
            global cur_rem

            events.add(event)
            await message.channel.send(f"event {event.name} succesfully added to the list!")
            reminders = generate_queue(events)
            await message.channel.send("succesfully generated new reminders!")

            if cur_rem is not None :
                cur_rem.cancel()
            if reminders.empty() :
                cur_rem = None
            else :
                cur_rem = asyncio.ensure_future(wait_reminder())
            
    
    elif message.content == "update events" :
        pass


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
    save_events(events)