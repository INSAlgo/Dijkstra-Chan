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
        lines.append(f"__from {self.webs}__")
        lines.append(f"main page : {self.link}")
        lines.append(f"To happen on : {self.time.strftime('%B %d, %Y, %H:%M')}")
        lines.append(self.description)

        return '\n'.join(lines)