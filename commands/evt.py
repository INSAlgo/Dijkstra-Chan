from datetime import datetime
from queue import PriorityQueue as PQ
import os, json, asyncio

import discord
from discord.ext.commands import Context

from classes.event import Event
from classes.reminder import Reminder, delays

from classes.codeforces_client import CF_Client

# notification channel from main script
notif_channel: discord.TextChannel

def fetch_notif_channel(channel: discord.TextChannel) :
    global notif_channel
    notif_channel = channel


# Functions about events

def update_events() -> int :
    global events
    prev_N = len(events)

    err_code, CF_events = cf_client.get_fut_cont_events()
    if err_code == 1 :
        print(CF_events)
    
    else :
        events |= CF_events

    return len(events) - prev_N

def msg_to_event(message: str) -> Event | None :
    lines = message.split('\n')[1:] # the first line is the command keyword

    attrs = {}

    attrs["name"] = lines[0]
    attrs["link"] = lines[1]
    attrs["webs"] = lines[2]
    attrs["desc"] = '\n'.join(lines[4:10])

    time = lines[3]
    try :
        data = map(int, (time[:4], time[5:7], time[8:10], time[11:13], time[14:16]))
        time = datetime(*data)
    except ValueError :
        return None
    
    return Event(attrs, time=time)

def remove_passed_events() -> None :
    to_remove = set()

    for event in events :
        if event.time <= datetime.now() :
            to_remove.add(event)
    
    events.difference_update(to_remove)

def save_events(file: str = "saved_data/events.json") :
    File = open(file, 'w')
    json.dump(list(map(Event.to_dict, events)), File)
    File.close()
    print("saved", len(events), "events to json.")

def load_events(file: str = "saved_data/events.json") -> set[Event] :
    for i in range(1, len(file.split('/'))) :
        sub_path = '/'.join(file.split('/')[:i])
        if not os.path.exists(sub_path) :
            os.mkdir(sub_path)
    
    if not os.path.exists(file) :
        File = open(file, 'x')
        File.write("[]")
        File.close()
    
    File = open(file)
    events = set(map(Event, json.load(File)))
    File.close()
    return events


# Functions about reminders

def generate_queue() -> PQ[Reminder] :
    reminders = PQ()

    for event in events :
        for delay in delays.keys() :
            rem = Reminder(event, delay)
            if rem.future :
                reminders.put(rem)

    return reminders

async def wait_reminder() :
    """
    Waits for reminders in the background of the bot
    """
    global reminders

    time = (reminders.queue[0].time - datetime.now()).total_seconds()
    print("waiting for a reminder...")
    await asyncio.sleep(time)
    await notif_channel.send("<@1051629248139505715>")  # event role mention
    await notif_channel.send(embed=reminders.get().embed())

    launch_reminder()

def launch_reminder() :
    global cur_rem
    if cur_rem is not None :
        cur_rem.cancel()
    if reminders.empty() :
        cur_rem = None
    else :
        cur_rem = asyncio.ensure_future(wait_reminder())


# vars initialisation :

events: set[Event] = load_events()
reminders: PQ[Reminder] = generate_queue()
cur_rem: asyncio.Task[None] | None = None
launch_reminder()

cf_client = CF_Client()


# Command function :

async def command_(
        admin_role: discord.Role, event_role: discord.Role,
        debug_channel: discord.TextChannel, command_channels: set[discord.TextChannel], 
        ctx: Context, func: str, *args: str
    ) :
    global events
    global reminders
    global cur_rem
    n_args = len(args)
    
    # Command to get/remove the role for events pings :
    if func == "toggle" :
        if ctx.channel not in command_channels :
            return

        if n_args > 0 :
            await ctx.channel.send("toggle does not have parameters")

        msg = "Role successfully "
        if event_role in ctx.author.roles :
            await ctx.author.remove_roles(event_role)
            msg += "removed."
        else :
            await ctx.author.add_roles(event_role)
            msg += "given."
        await ctx.channel.send(msg)

    # Command to display events :
    elif func == "get" :
        if ctx.channel not in command_channels :
            return
        
        if n_args == 0 :
            nb = 3
        elif n_args == 1 :
            nb = int(args[0])
        else :
            nb = int(args[0])
            await ctx.channel.send("get has at most 1 parameter : the number of events to show")
        
        remove_passed_events()
        list_events = list(events)
        list_events.sort()

        for event in list_events[:nb] :
            await ctx.channel.send(embed=event.embed())
    
    # (admin) Command to update the list events :
    elif func == "update" :
        if admin_role not in ctx.author.roles or ctx.channel != debug_channel :
            return

        if n_args > 0 :
            await ctx.channel.send("update does not have parameters")

        remove_passed_events()
        N = update_events()
        await ctx.channel.send(f"{N} new event(s) found!")
        save_events()

        if N > 0 :
            reminders = generate_queue(events)

            launch_reminder()
    
    # (admin) Command to add an event :
    elif func == "add" :
        if admin_role not in ctx.author.roles or ctx.channel != debug_channel :
            return

        event = msg_to_event(ctx.message.content)

        if event is None :
            await ctx.channel.send("please format the date as YYYY/MM/DD HH:MM")

        else :
            events.add(event)
            await ctx.channel.send(f"event {event.name} succesfully added to the list!")
            reminders = generate_queue()
            await ctx.channel.send("succesfully generated new reminders!")
            save_events()

            launch_reminder()