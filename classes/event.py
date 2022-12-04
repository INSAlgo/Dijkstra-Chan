from __future__ import annotations
from datetime import datetime
import json

# As a format help (possibility to add more) :
websites = {"CodeForces"}

class Event :
    def __init__(self, attrs: dict[str, str | int], time: datetime | None = None) :
        """### Constructor of an event

        ## Parameters :
        - attrs : :class:`dict[str, str | int]`
            - Must contains 4 text fields : name, link, webs (website) and desc (description).   
        - time : :class:`datetime`
            - Indicates the time of the event.
            - Can be None if `{"time": <timestamp in second>}` is added to `attrs`.

        ## Returns :
        - None
        """

        assert {"name", "link", "webs", "desc"}.issubset(attrs.keys())
        self.name = attrs["name"]
        self.link = attrs["link"]
        self.webs = attrs["webs"]
        if self.webs == "" :
            self.webs = " "
        self.desc = attrs["desc"]
        self.time = None

        if "time" in attrs.keys() :
            time = attrs["time"]

            if isinstance(time, str) :
                try :
                    time = float(time)
                except :
                    print("string for timestamp (number of seconds since epoch) should be readable as a float")
            
            if isinstance(time, float) :
                time = int(time)
            if isinstance(time, int) :
                self.time = datetime.fromtimestamp(time)
            else :
                print(f"time attribute not properly typed : should be int, float or string, is {type(time)} instead")

        elif time is not None :
            if isinstance(time, datetime) :
                self.time = time
            else :
                print(f"Parameter time should be datetime object, instead it's {type(time)}")
        else :
            print(f"No datetime or timestamp provided for this event")
    
    def to_dict(self) :
        return {
            "name" : self.name, "link" : self.link, "webs" : self.webs,
            "time" : int(self.time.timestamp()), "desc" : self.desc
        }
    
    def __lt__(self, other: Event) :
        return self.time < other.time
    
    def __eq__(self, other: Event) :
        return (self.webs, self.name, self.time.timestamp()) == (other.webs, other.name, other.time.timestamp())
    
    def __hash__(self) :
        # For identification, to avoid duplicate events
        return self.name.__hash__()

    def msg(self) -> str :
        """
        A method returning a representation of the event as a formated discord message.
        """

        lines = []
        lines.append(f"**{self.name}**")
        lines.append(f"*from {self.webs}*")
        lines.append(f"main page : {self.link}")
        lines.append(f"To happen on : {self.time.strftime('%B %d, %Y, %H:%M')}")
        lines.append(self.desc)

        return '\n'.join(lines)

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

def remove_passed_events(events: set[Event]) -> set[Event] :
    new_events = set()

    for event in events :
        if event.time > datetime.now() :
            new_events.add(event)
    
    return new_events

def save_events(events: set[Event], file: str = "saved_data/events.json") :
    File = open(file, 'w')
    json.dump(list(map(Event.to_dict, events)), File)
    File.close()

def load_events(file: str = "saved_data/events.json") -> set[Event] :
    File = open(file)
    events = set(map(Event, json.load(File)))
    File.close()
    return events