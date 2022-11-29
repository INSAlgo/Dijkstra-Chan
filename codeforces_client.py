from client_template import Client
from datetime import datetime, timedelta

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

def get_future_contests(nb: int = 0) -> tuple[int, list[dict] | str] :
    err_code, res = get_contests()

    if err_code == 1 :
        return "client.get error : " + res
    elif err_code == 2 :
        return "CodeForces response not OK : " + res
    
    # nb < 1 -> return all contests to come
    if nb < 1 :
        nb = len(res)
    
    res.sort(key=lambda c : c["startTimeSeconds"])

    contests = []

    for contest in res[:nb] :
        lines = []

        lines.append(f"**{contest['name']}**")
        
        if "startTimeSeconds" in contest.keys() :
            date: datetime = datetime.fromtimestamp(contest["startTimeSeconds"])
            lines.append("Will start on " + date.strftime("%B %d, %Y, %H:%M"))
        else :
            lines.append("Start date unknown")
        
        m = contest["durationSeconds"] // 60
        lines.append(f"For a duration of {m//60} hours and {m%60} minutes")
        
        if "difficulty" in contest.keys() :
            dif = contest["difficulty"] + "/5"
        else :
            dif = "unknown"
        if "kind" in contest.keys() :
            kind = contest["kind"]
        else :
            kind = "unknown"
        lines.append(f"difficulty : {dif}, kind : {kind}")

        if "description" in contest.keys() :
            lines.append(contest["description"])
        
        contests.append('\n'.join(lines))
    
    return '\n\n'.join(contests)