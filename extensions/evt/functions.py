from datetime import datetime, timedelta
from queue import PriorityQueue as PQ
import os, json, asyncio
from traceback import format_exc

from discord.ext.tasks import loop

from bot import bot

from extensions.evt.event_class import Event
from extensions.evt.reminder_class import Reminder, delays

from extensions.evt.codeforces_client import CF_Client


# Functions about events

def update_events() -> int :
    prev_N = len(events)

    err_code, CF_events = cf_client.get_fut_cont_events()
    if err_code == 1 :
        print(CF_events)
    
    else :
        events.update(CF_events)

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

def load_events(file: str = "saved_data/events.json") :
    for i in range(1, len(file.split('/'))) :
        sub_path = '/'.join(file.split('/')[:i])
        if not os.path.exists(sub_path) :
            os.mkdir(sub_path)
    
    if not os.path.exists(file) :
        File = open(file, 'x')
        File.write("[]")
        File.close()
    
    File = open(file)
    events.update(set(map(Event, json.load(File))))
    File.close()


# Functions about reminders

def generate_queue() -> None :
    reminders.queue.clear()

    for event in events :
        for delay in delays.keys() :
            rem = Reminder(event, delay)
            if rem.future :
                reminders.put(rem)

async def wait_reminder() :
    """
    Waits for reminders in the background of the bot
    """
    time = (reminders.queue[0].time - datetime.now()).total_seconds()
    print("Waiting for a reminder at :", reminders.queue[0].time)
    try :
        await asyncio.sleep(time)
    except asyncio.CancelledError :
        print("Wait reminders cancelled")
        return
    
    await bot.client.wait_until_ready()
    await bot.channels["notifs"].send(bot.roles["events"])  # event role mention
    await bot.channels["notifs"].send(embed=reminders.get().embed())

    launch_reminder()

def launch_reminder() :
    global cur_rem

    if cur_rem is not None :
        cur_rem.cancel()
    if reminders.empty() :
        cur_rem = None
    else :
        cur_rem = asyncio.create_task(wait_reminder())


# globals definition :

events: set[Event] = set()
reminders: PQ[Reminder] = PQ()
cur_rem: asyncio.Task[None] | None = None
cf_client: CF_Client = CF_Client()


# Discord task loop to update events and reminders daily :

@loop(hours=24)
async def daily_update() :
    remove_passed_events()
    update_events()
    save_events()

    generate_queue()
    launch_reminder()

    print("Waiting for next daily update at :", datetime.now()+timedelta(days=1))

@daily_update.before_loop
async def before_loop() :
    load_events()
    await bot.client.wait_until_ready()