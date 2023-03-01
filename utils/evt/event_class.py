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

        # Really complicated time parsing because fuck this

        self.valid_time = False
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
                self.valid_time = True
            else :
                print(f"time attribute not properly typed : should be int, float or string, is {type(time)} instead")

        elif time is not None :
            if isinstance(time, datetime) :
                self.time = time
                self.valid_time = True
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
        if self.valid_time :
            time = int(self.time.timestamp())
        else :
            time = self.time
        
        return {
            "name" : self.name, "link" : self.link, "webs" : self.webs,
            "time" : time, "desc" : self.desc,
            "id" : self.id
        }
    
    def __lt__(self, other: Event) :
        if not self.valid_time :
            return True
        if not other.valid_time :
            return False
        
        return self.time < other.time
    
    def __eq__(self, other: Event) :
        return self.id == other.id
    
    def __hash__(self) :
        if type(self.id) == int :
            return self.id
        if type(self.id) == str :
            return sum(ord(char) for char in self.id)
        return self.name.__hash__()
    
    def embed(self) -> Embed :
        res = Embed(title=self.name)

        res.description = f"*From {self.webs}*\n" + self.desc

        if re.match(regex, self.link) is not None :
            res.url = self.link
        
        if self.valid_time :
            timestamp = int(self.time.timestamp())
            res.add_field(name="To happen on :", value=f"<t:{timestamp}:f> (<t:{timestamp}:R>)")
        else :
            res.add_field(name="Invalid Time :angry:")

        return res