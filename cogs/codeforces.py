from discord.ext.commands import Cog
from main import CustomBot

from utils.client_template import Client

from modules.evt.event_class import Event


class CodeforcesClient(Client, Cog) :

    def __init__(self, bot: CustomBot):
        Client.__init__(self, "codeforces.com/api/")
        self.bot = bot
        self.contests = []

    def get_contests(self, statuses: set[str] = {"BEFORE"}) -> tuple[int, str] :
        # Getting every finished contest would be too heavy
        statuses.difference_update({"FINISHED"})


        if not self.get(route="contest.list", payload={"gym": "false"}) :
            return 1, self.lr_error()

        json = self.lr_response()

        if json["status"] != "OK" :
            return 2, json["comment"]

        all_contests = json["result"]
        self.contests = []

        for i in range(len(all_contests)) :
            if all_contests[i]["phase"] in statuses :
                self.contests.append(all_contests[i])

        return 0, ""

    def CF_contest_event(self, contest: dict[str]) -> tuple[int, Event | str] :
        if "startTimeSeconds" not in contest :
            return 1, "no timestamp"
        
        attrs = {}

        attrs["name"] = contest["name"]
        attrs["link"] = "https://codeforces.com/contests/" + str(contest["id"])
        attrs["webs"] = "CodeForces"
        attrs["time"] = contest["startTimeSeconds"]

        m = contest["durationSeconds"] // 60
        attrs["desc"] = f"Will be {m//60} hour(s) and {m%60} minutes long"
        if "description" in contest.keys() :
            attrs["desc"] += '\n' + contest["desc"]
        
        return 0, Event(attrs)

    def get_fut_cont_events(self) -> tuple[int, set[Event] | str]:
        err_code, res = self.get_contests()

        if err_code == 1 :
            return 1, "client.get() error : " + res
        elif err_code == 2 :
            return 1, "CodeForces response not OK : " + res
        
        events = set()

        for contest in self.contests :
            err_code, event = self.CF_contest_event(contest)

            if err_code == 1 :
                # contest without a date
                continue
            
            events.add(event)
        
        return 0, events

async def setup(bot):
    await bot.add_cog(CodeforcesClient(bot))
