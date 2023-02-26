from __future__ import annotations
from datetime import datetime
import re

from discord import Embed

# As a format help (possibility to add more) :
websites = {"CodeForces"}

# regex to check link validity :
regex = re.compile(
    r'^(?:http|ftp)s?://' # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
    r'localhost|' #localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
    r'(?::\d+)?' # optional port
    r'(?:/?|[/?]\S+)$',
    re.IGNORECASE
)

class Event :
    def __init__(self, attrs: dict[str, str | int], time: datetime | None = None) :
        """## Constructor of an event

        ### Parameters :
        - attrs : :class:`dict[str, str | int]`
            - Must contains 4 text fields : name, link, webs (website) and desc (description).   
        - time : :class:`datetime`
            - Indicates the time of the event.
            - Can be None if `{"time": <timestamp in second>}` is added to `attrs`.

        ### Returns :
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
        
        if "id" in attrs.keys() :
            self.id = attrs["id"]

        elif self.webs == "CodeForces" :
            self.id = "CF" + self.link.split("/")[-1]
        
        else :
            self.id = self.name
    
    def to_dict(self) :
        return {
            "name" : self.name, "link" : self.link, "webs" : self.webs,
            "time" : int(self.time.timestamp()), "desc" : self.desc,
            "id" : self.id
        }
    
    def __lt__(self, other: Event) :
        return self.time < other.time
    
    def __eq__(self, other: Event) :
        return self.id == other.id
    
    def __hash__(self) :
        # For identification, to avoid duplicate events
        if type(self.id) == int :
            return self.id
        if type(self.id) == str :
            return sum(ord(char) for char in self.id)
        return self.name.__hash__()
        

    def msg(self) -> str :
        # Unused
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
    
    def embed(self) -> Embed :
        res = Embed(title=self.name)

        res.description = f"*From {self.webs}*\n" + self.desc

        if re.match(regex, self.link) is not None :
            res.url = self.link
        
        res.add_field(name="To happen on :", value=self.time.strftime('%B %d, %Y, %H:%M'))

        return res