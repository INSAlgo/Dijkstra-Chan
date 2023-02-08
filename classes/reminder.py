from __future__ import annotations

from datetime import datetime, timedelta
from queue import PriorityQueue as PQ

from discord import Embed

from classes.event import Event

# For message formating :
delays = {
    "5min": timedelta(seconds=60*5),
    "hour": timedelta(seconds=3600),
    "day": timedelta(days=1)
}

messages = {
    "5min": ":warning: **Get ready, this event is in 5 minutes!** :",
    "hour": ":alarm_clock: **Friendly reminder that this event is in an hour** :",
    "day": ":bell: **New event for tomorrow** :"
}

colors = {
    "5min": 16711680,
    "hour": 16750848,
    "day": 1127128
}

class Reminder :
    def __init__(self, event: Event, delay: str) :
        assert delay in delays
        self.delay: str = delay
        self.time: datetime = event.time - delays[delay]
        self.event: Event = event
        self.future: bool = (self.time > datetime.now())
    
    def __lt__(self, other: Reminder) :
        return self.time < other.time
    
    def __str__(self) :
        return self.msg() + "\n\n"
    
    def msg(self) :
        # Unused
        return messages[self.delay] + "\n>>> " + self.event.msg()
    
    def embed(self) -> Embed  :    
        if self.event.link != "" :
            desc = f"**[{self.event.name}]({self.event.link})**"
        else :
            desc = f"**{self.event.name}**"
        
        if self.event.desc != "" :
            desc += '\n' + self.event.desc
        
        res = Embed(title=messages[self.delay], description=desc, color=colors[self.delay])
        
        res.add_field(name="From", value=f"*{self.event.webs}*", inline=False)
        res.add_field(name="To happen on :", value=self.event.time.strftime('%B %d, %Y, %H:%M'), inline=False)

        return res