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

def get_fut_cont_message(nb: int = 0) -> tuple[int, list[dict] | str] :
    err_code, res = get_contests()

    if err_code == 1 :
        return "client.get error : " + res
    elif err_code == 2 :
        return "CodeForces response not OK : " + res
    
    # nb < 1 -> return all contests to come
    if nb < 1 :
        nb = len(res)
    
    res.sort(key=lambda c : c["startTimeSeconds"] if ("startTimeSeconds" in c) else float("inf"))

    contests = []

    i = 0
    for contest in res[:nb] :
        lines = []

        lines.append(f"**{contest['name']}**")
        
        if "startTimeSeconds" in contest.keys() :
            date: datetime = datetime.fromtimestamp(contest["startTimeSeconds"])
            lines.append("Will start on " + date.strftime("%B %d, %Y, %H:%M"))
        else :
            lines.append("Start date unknown")
        
        m = contest["durationSeconds"] // 60
        lines.append(f"For a duration of {m//60} hour(s) and {m%60} minutes")
        
        ## Usually "unknwon", so it's useless to add them
        # if "difficulty" in contest.keys() :
        #     dif = contest["difficulty"] + "/5"
        # else :
        #     dif = "unknown"
        # if "kind" in contest.keys() :
        #     kind = contest["kind"]
        # else :
        #     kind = "unknown"
        # lines.append(f"difficulty : {dif}, kind : {kind}")

        if "description" in contest.keys() :
            lines.append(contest["description"])
        
        contests.append('\n'.join(lines))
    
    return '\n\n'.join(contests)

def CF_contest_event(contest: dict[str]) -> tuple[int, Event | str] :
    if "startTimeSeconds" not in contest :
        return 1, "no timestamp"
    
    name = contest["name"]
    link = "https://codeforces.com/contests/" + str(contest["id"])
    website = "CodeForces"

    m = contest["durationSeconds"] // 60
    desc = f"Will be {m//60} hour(s) and {m%60} minutes long"
    if "description" in contest.keys() :
        desc += '\n' + contest["desc"]
    
    timestamp = datetime.fromtimestamp(contest["startTimeSeconds"])
    
    return 0, Event(name, link, website, desc, timestamp)

def get_fut_cont_reminders(test=False) -> tuple[int, list[Event] | str]:
    err_code, res = get_contests()

    if err_code == 1 :
        return 1, "client.get() error : " + res
    elif err_code == 2 :
        return 1, "CodeForces response not OK : " + res
    
    reminders = []

    for contest in res :
        err_code, event = CF_contest_event(contest)

        if err_code == 1 :
            # contest without a date
            continue
        
        reminders.append(Reminder(event, "5min"))
        reminders.append(Reminder(event, "hour"))
        reminders.append(Reminder(event, "day"))
    
    if test :
        # Sets reminders to test messages
        reminders.append(Reminder(
            Event(
                "Test_day", "", "", "test for day reminder",
                datetime.now() + timedelta(days=1, seconds=60)
            ),
            "day"
        ))
        reminders.append(Reminder(
            Event(
                "Test_hour", "", "", "test for hour reminder",
                datetime.now() + timedelta(days=1, seconds=3720)
            ),
            "hour"
        ))
        reminders.append(Reminder(
            Event(
                "Test_5min", "", "", "test for 5min reminder",
                datetime.now() + timedelta(days=1, seconds=480)
            ),
            "5min"
        ))
    
    return 0, reminders