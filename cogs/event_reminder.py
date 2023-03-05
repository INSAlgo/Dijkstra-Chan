from datetime import datetime, timedelta
from queue import PriorityQueue as PQ
import asyncio, json, os

import discord
import discord.ext.commands as cmds
from discord.ext.tasks import loop
from main import CustomBot

from utils.IDs import *
from utils.checks import *

from cogs.codeforces import CodeforcesClient

from utils.evt.event_class import Event
from utils.evt.reminder_class import Reminder, delays
import logging
logger = logging.getLogger(__name__)

class EventReminder(cmds.Cog) :

    def __init__(self, bot: CustomBot) -> None:

        self.bot = bot
        self.event_role: discord.Role = None
        self.event_channel: discord.TextChannel = None

        self.events: set[Event] = set()
        self.reminders: PQ[Reminder] = PQ()
        self.cur_rem: asyncio.Task[None] | None = None

        self.cf_client: CodeforcesClient = bot.get_cog("CodeforcesClient")

    async def cog_unload(self):
        self.save_events()
        return await super().cog_unload()

    @commands.Cog.listener()
    async def on_ready(self):
        self.daily_update.start()
        logger.info("updated events")


    # Methods about events :

    def update_events(self) -> int :
        prev_N = len(self.events)

        err_code, res = self.cf_client.get_fut_cont_events()
        if err_code == 1 :
            logger.error(res)
        
        else :
            self.events.update(res)

        return len(self.events) - prev_N
    
    @staticmethod
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
            logger.error("wait reminders cancelled")
            return
        
        await self.event_channel.send(self.event_role.mention)  # event role mention
        await self.event_channel.send(embed=self.reminders.get().embed())

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
        if ctx.invoked_subcommand is None:
            await self.get(ctx)
    
    @evt.command()
    async def help(self, ctx: cmds.Context) :
        await ctx.send("TODO :)")

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
        self.remove_passed_events()
        list_events = list(self.events)
        list_events.sort()

        for event in list_events[:N] :
            await ctx.channel.send(embed=event.embed())

    @evt.command()
    @cmds.has_role(ADMIN)
    async def update(self, ctx: cmds.Context) :
        self.remove_passed_events()
        N = self.update_events()
        await ctx.channel.send(f"{N} new event(s) found!")
        self.save_events()

        if N > 0 :
            self.generate_queue()
            self.launch_reminder()

    @evt.command()
    @cmds.has_role(ADMIN)
    async def add(self, ctx: cmds.Context) :
        
        event = self.msg_to_event(ctx.message.content)

        if event is None :
            await ctx.channel.send("please format the date as YYYY/MM/DD HH:MM")

        else :
            self.events.add(event)
            await ctx.channel.send(f"event {event.name} succesfully added to the list!")
            self.generate_queue()
            await ctx.channel.send("succesfully generated new reminders!")
            self.save_events()

            self.launch_reminder()

async def setup(bot):
    await bot.add_cog(EventReminder(bot))
