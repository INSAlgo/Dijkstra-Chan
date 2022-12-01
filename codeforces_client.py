from client_template import Client
from datetime import datetime, timedelta

from event import Event
from reminder import Reminder

CF_client = Client("codeforces.com/api/")

def get_contests(statuses: set[str] = {"BEFORE"}) -> tuple[int, list[dict] | str] :
    # Getting every finished contest would be too heavy
    statuses.difference_update({"FINISHED"})


    if not CF_client.get(route="contest.list", payload={"gym": "false"}) :
        return 1, CF_client.lr_error()

    json = CF_client.lr_response(json=True)

    if json["status"] != "OK" :
        return 2, json["comment"]

    all_contests = json["result"]
    res = []

    for i in range(len(all_contests)) :
        if all_contests[i]["phase"] in statuses :
            res.append(all_contests[i])

    return 0, res

def CF_contest_event(contest: dict[str]) -> tuple[int, Event | str] :
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

def get_fut_cont_events() -> tuple[int, set[Event] | str]:
    err_code, res = get_contests()

    if err_code == 1 :
        return 1, "client.get() error : " + res
    elif err_code == 2 :
        return 1, "CodeForces response not OK : " + res
    
    events = set()

    for contest in res :
        err_code, event = CF_contest_event(contest)

        if err_code == 1 :
            # contest without a date
            continue
        
        events.add(event)
    
    return 0, events