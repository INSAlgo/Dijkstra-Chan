import discord
import asyncio
from argparse import ArgumentParser
from datetime import datetime

import re
from queue import PriorityQueue as PQ

from token_error import TokenError
from codeforces_client import get_fut_cont_events
from github_client import GH_Client
from event import Event, msg_to_event, save_events, load_events, remove_passed_events
from reminder import Reminder, generate_queue


intents = discord.Intents.all()
client = discord.Client(intents=intents)
gh_client: GH_Client = None
server: discord.Guild = None

notif_channel: discord.TextChannel = None
debug_channel: discord.TextChannel = None

admin_role: discord.Role = None
bureau_role: discord.Role = None

events: set[Event] = set()
reminders: PQ[Reminder] = PQ()
cur_rem: asyncio.Task[None] | None = None

File = open("help.txt")
help_txt = File.read()
File.close()
File = open("admin_help.txt")
admin_help_txt = File.read()
File.close()

rec = 1

#=================================================================================================================================================================

def update_events() -> int :
    global events
    prev_N = len(events)

    err_code, CF_events = get_fut_cont_events()
    if err_code == 1 :
        print(CF_events)
    
    else :
        events |= CF_events

    return len(events) - prev_N

async def connect_gh_client() :
    global gh_client
    try :
        gh_client = GH_Client(gh_token)
    except TokenError :
        await debug_channel.send("The github token is wrong or has expired, please generate a new one. See README for more info.")
        raise TokenError
    except Exception as err :
        await debug_channel.send(err)
        raise Exception

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


#=================================================================================================================================================================

@client.event
async def on_ready() :
    global events
    events = load_events()
    
    global reminders
    reminders = generate_queue(events)

    global notif_channel
    notif_channel = discord.utils.get(client.get_all_channels(), name="annonces-automatiques")
    global debug_channel
    debug_channel = discord.utils.get(client.get_all_channels(), name="dijkstra-chan-debug")

    global server
    server = notif_channel.guild

    global admin_role
    admin_role = discord.utils.get(server.roles, name="Admin bot")
    global bureau_role
    admin_role = discord.utils.get(server.roles, name="Bureau")

    global cur_rem
    if cur_rem is not None :
        cur_rem.cancel()
    if reminders.empty() :
        cur_rem = None
    else :
        cur_rem = asyncio.ensure_future(wait_reminder())

    await connect_gh_client()
    _, msg = gh_client.reload_repo_tree()
    await debug_channel.send(msg)


#=================================================================================================================================================================

@client.event
async def on_message(message: discord.Message):
    global events
    global reminders
    global cur_rem
    global rec

    # Silly recursive function
    if re.fullmatch("^factorial [0-9]+$", message.content) is not None :
        nb = int(message.content.split(' ')[-1])
        if nb < 0 :
            await message.channel.send(f"number cannot be negative !")
        elif nb > 20 :
            await message.channel.send(f"factorial {nb-1}\njust joking, I'm not doing that")
        elif nb <= 1 :
            await message.channel.send(f"result : {rec}")
            rec = 1
        else :
            rec *= nb
            await message.channel.send(f"factorial {nb-1}")
        return

    # Avoid answering itself
    if message.author == client.user:
        return

    # Help message :
    if message.content.lower() == "help me dijkstra-chan!" :
        if admin_role in message.author.roles and message.channel == debug_channel :
            await debug_channel.send(admin_help_txt)
        else :
            await message.channel.send(help_txt)

    # (admin) Command to add an event :
    elif message.content.startswith("add event") :
        if admin_role not in message.author.roles :
            return
        
        event = msg_to_event(message.content)

        if event is None :
            await message.channel.send("please format the date as YYYY/MM/DD HH:MM")
        
        else :

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
    
    # Command to display events :
    elif re.fullmatch("^get events( [0-9]+)?$", message.content) is not None :
        events = remove_passed_events(events)
        list_events = list(events)
        list_events.sort()
        
        # Parsing the number of events wanted :
        if message.content[-1].isnumeric() :
            nb = int(message.content.split(' ')[-1])
        else :
            nb = len(list_events)
        
        await message.channel.send('\n\n'.join([ev.msg() for ev in list_events[:nb]]))
    
    # (admin) Command to fetch events from websites :
    elif message.content == "update events" :
        if admin_role not in message.author.roles :
            return
        
        events = remove_passed_events(events)
        N = update_events()
        await message.channel.send(f"{N} new event(s) found!")

        if N > 0 :
            reminders = generate_queue(events)

            if cur_rem is not None :
                cur_rem.cancel()
            if reminders.empty() :
                cur_rem = None
            else :
                cur_rem = asyncio.ensure_future(wait_reminder())
    
    # (admin) Command to reload solutions repo tree cache :
    elif message.content == "reload solutions tree" :
        if admin_role not in message.author.roles :
            return
        
        _, msg = gh_client.reload_repo_tree()
        await message.channel.send(msg)

    # Command to get the solution of an exercise :
    elif re.fullmatch("^get solution [A-Z]{2} .*", message.content) is not None :
        webs = message.content.split(" ")[2]
        file_name = " ".join(message.content.split(" ")[3:])

        _, raw_message = gh_client.search_correction(webs, file_name)
        await message.channel.send(raw_message)
    
    # (admin) Command to change github token :
    elif message.content.startswith("update github token ") :
        if bureau_role not in message.author.roles :
            return
        
        gh_token = message.content.split(' ')[-1]
        await connect_gh_client()


#=================================================================================================================================================================

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

    parser.add_argument(
        '-ght', '--github_token',
        help="The file to read the github token from, or the token itself if -nf.",
        action="store",
        default="github_token",
        required=False
    )

    parser.add_argument(
        '-ghnf', '--gh_is_not_file',
        help="If given, reads the file given in -ght, else takes -ght as the github token.",
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

    if args.gh_is_not_file :
        gh_token = args.github_token
    
    else :
        File = open(args.github_token)
        gh_token = File.readline().strip('\n')
        File.close()

    client.run(token)
    save_events(events)
    print("saved", len(events), "events to json.")