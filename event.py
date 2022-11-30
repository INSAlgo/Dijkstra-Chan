from datetime import datetime

# As a format help (possibility to add more) :
websites = {"CodeForces"}

class Event :
    def __init__(self, name: str, link: str, website: str, description: str, time: int | datetime) :
        self.name = name
        self.link = link
        self.webs = website
        self.description = description

        if type(time) in {"int", "float"} :
            self.time = datetime.fromtimestamp(time)
        elif type(time) is datetime :
            self.time = time
        else :
            print(f"Parameter time should be timestamp (int or float) or datetime object, instead it's {type(time)}")
            self.time = None
    
    def msg(self) -> str :
        """
        A method returning a representation of the event as a formated discord message.
        """

        lines = []
        lines.append(f"**{self.name}**")
        lines.append(f"*from {self.webs}*")
        lines.append(f"main page : {self.link}")
        lines.append(f"To happen on : {self.time.strftime('%B %d, %Y, %H:%M')}")
        lines.append(self.description)

        return '\n'.join(lines)

def msg_to_event(message: str) -> Event | None :
    lines = message.split('\n')[1:] # the first line is the command keyword
    name = lines[0]
    link = lines[1]
    website = lines[2]

    time = lines[3]
    try :
        data = map(int, (time[:4], time[5:7], time[8:10], time[11:13], time[14:16]))
        time = datetime(*data)
    except ValueError :
        return None
    
    return Event(name, link, website, '\n'.join(lines[4:]), time)