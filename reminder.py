from __future__ import annotations

from datetime import datetime, timedelta

from event import Event

# For message formating :
delays = {
    "5min": timedelta(seconds=60*5),
    "hour": timedelta(seconds=3600),
    "day": timedelta(days=1)
}

messages = {
    "5min": ":warning: **Get ready, this event is in 5 minutes** :\n",
    "hour": ":alarm_clock: **Friendly reminder that this event is in an hour** :\n",
    "day": ":bell: **New event for tomorrow** :\n"
}

class Reminder :
    def __init__(self, event: Event, delay: str) :
        assert delay in delays
        self.delay: str = delay
        self.time: datetime = event.time - delays[delay]
        self.event: Event = event
    
    def __lt__(self, other: Reminder) :
        return self.time < other.time
    
    def __str__(self) :
        return self.msg() + "\n\n"
    
    def msg(self) :
        return messages[self.delay] + self.event.msg()