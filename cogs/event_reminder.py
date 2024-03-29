from datetime import datetime, timedelta
from queue import PriorityQueue as PQ
from logging import getLogger
import asyncio, json, os

import discord
import discord.ext.commands as cmds
from discord.ext.tasks import loop

from utils.codeforces import cf_client

from modules.evt.event_class import Event
from modules.evt.reminder_class import Reminder, delays

from utils.ids import *
from utils.checks import *

from main import CustomBot


logger = getLogger(__name__)

class EventReminder(cmds.Cog, name="Events reminder"):
    """
    Commands and internal modules about coding events like contests
    Operates reminders and some APIs to fetch events
    """

    def __init__(self, bot: CustomBot) -> None:

        self.bot = bot
        self.event_role: discord.Role = None
        self.event_channel: discord.TextChannel = None

        self.events: set[Event] = set()
        self.reminders: PQ[Reminder] = PQ()
        self.cur_rem: asyncio.Task[None] | None = None

    async def cog_unload(self):
        self.save_events()
        return await super().cog_unload()

    @commands.Cog.listener()
    async def on_ready(self):
        self.daily_update.start()
        logger.info("updated events")

        self.event_role = self.bot.insalgo.get_role(ids.EVENT_PING)
        self.event_channel = self.bot.get_channel(ids.EVENTS)

        brief = f"Toggles the {self.event_role.mention} role"
        self.toggle.brief = brief
        help_ = brief + f"This role is automatically pinged when I send a reminder to {self.event_channel.mention}"
        self.toggle.help = help_


    # Methods about events :

    def update_events(self) -> int :
        prev_N = len(self.events)

        err_code, res = cf_client.get_fut_cont_events()
        if err_code == 1 :
            logger.error(res)
        
        else :
            self.events.update(res)

        return len(self.events) - prev_N

    def remove_passed_events(self) -> None :
        to_remove = set()

        for event in self.events :
            if event.time <= datetime.now() :
                to_remove.add(event)
        
        self.events.difference_update(to_remove)

    def save_events(self) :
        logger.info("saving events, DO NOT CLOSE APP!")
        File = open("saved_data/events.json", 'w')
        json.dump(list(map(Event.to_dict, self.events)), File)
        File.close()
        logger.info(f"saved {len(self.events)} events to json.")

    def load_events(self) :
        if not os.path.exists("saved_data") :
            os.mkdir("saved_data")
        
        file = "saved_data/events.json"
        if not os.path.exists(file) :
            File = open(file, 'x')
            File.write("[]")
            File.close()
        
        File = open(file)
        self.events = set(map(Event, json.load(File)))
        File.close()

    # Methods about reminders :

    def generate_queue(self) :
        self.reminders.queue.clear()

        for event in self.events :
            for delay in delays.keys() :
                rem = Reminder(event, delay)
                if rem.future :
                    self.reminders.put(rem)

    async def wait_reminder(self) :
        """
        Waits for reminders in the background of the bot
        """
        time = (self.reminders.queue[0].time - datetime.now()).total_seconds()
        logger.info(f"waiting for a reminder at : {self.reminders.queue[0].time}")
        try :
            await asyncio.sleep(time)
        except asyncio.CancelledError :
            logger.warning("wait reminders cancelled")
            return
        
        await self.event_channel.send(content=self.event_role.mention, embed=self.reminders.get().embed())

        self.launch_reminder()

    def launch_reminder(self) :
        if self.cur_rem is not None :
            self.cur_rem.cancel()
        if self.reminders.empty() :
            self.cur_rem = None
        else :
            self.cur_rem = asyncio.create_task(self.wait_reminder())

    # Discord task loop to update events and reminders daily :

    @loop(hours=24)
    async def daily_update(self) :
        self.remove_passed_events()
        self.update_events()
        self.save_events()

        self.generate_queue()
        self.launch_reminder()

        logger.info(f"waiting for next daily update at : {datetime.now()+timedelta(days=1)}")

    @daily_update.before_loop
    async def before_loop(self) :
        self.load_events()
        await self.bot.wait_until_ready()

    # Commands :

    @cmds.group(pass_context=True)
    @in_channel(COMMANDS, force_guild=False)
    async def evt(self, ctx: cmds.Context) :
        """
        Commands about coding events and reminders
        Shortcut for `!evt get 3`
        """
        if ctx.invoked_subcommand is None:
            await self.get(ctx)

    @evt.command()
    async def toggle(self, ctx: cmds.Context) :
        msg = "Role successfully "
        if self.event_role in ctx.author.roles :
            await ctx.author.remove_roles(self.event_role)
            msg += "removed."
        else :
            await ctx.author.add_roles(self.event_role)
            msg += "given."
        await ctx.channel.send(msg)
    
    @evt.command()
    async def get(self, ctx: cmds.Context, N: int = 3) :
        """
        Command to get a list of the next N events (N=3 by default)
        """
        self.remove_passed_events()
        list_events = list(self.events)
        list_events.sort()

        for event in list_events[:N] :
            await ctx.channel.send(embed=event.embed())

    @evt.command(hidden=True)
    @cmds.has_role(ADMIN)
    async def update(self, ctx: cmds.Context) :
        """
        Fetches events from websites and generates reminders
        Currently, only CodeForces is polled for rounds
        """
        self.remove_passed_events()
        N = self.update_events()
        await ctx.channel.send(f"{N} new event(s) found!")
        self.save_events()

        if N > 0 :
            self.generate_queue()
            self.launch_reminder()

    @evt.command(hidden=True)
    @cmds.has_role(ADMIN)
    async def add(self, ctx: cmds.Context, name: str, link: str, origin: str, timestamp: int, *, description: str) :
        """
        Creates a new custom event with its reminders
        In most cases, <name> is the identifier of the event
        Add double quotes around <link> if it has spaces
        <origin> is where the event is from, for example "CodeForces" or "HackerRank"
        Go [here](https://www.timestamp-converter.com/) to convert a date-time into a timestamp
        <description> is the tail of your command, spaces and newlines included
        """
        
        event = Event({
            "name": name,
            "link": link,
            "webs": origin,
            "desc": description
        }, datetime.fromtimestamp(timestamp))

        if event is None :
            await ctx.channel.send("please format the date as YYYY/MM/DD HH:MM")

        else :
            if event in self.events :
                await ctx.channel.send(f"event {event.name} already exists, replacing...")
                self.events.discard(event)
            
            self.events.add(event)
            await ctx.channel.send(f"event {event.name} succesfully added to the list!")

            self.generate_queue()
            await ctx.channel.send("succesfully generated new reminders!")
            self.save_events()

            self.launch_reminder()

async def setup(bot: CustomBot):
    await bot.add_cog(EventReminder(bot))
