#=================================================================================================================================================================
# IMPORTS

import os
import asyncio
from datetime import datetime
import re
from queue import PriorityQueue as PQ
from requests import get as rqget
from requests import post

import discord
from discord.ext import commands

from classes.token_error import TokenError
from classes.codeforces_client import CF_Client
from classes.github_client import GH_Client
from classes.openai_client import OPENAI_Client
from classes.event import Event, msg_to_event, save_events, load_events, remove_passed_events
from classes.reminder import Reminder, generate_queue

from functions.embeding import embed, embed_help
from functions.geometry_read import draw_submission
from functions.geometry_check import check


#=================================================================================================================================================================
# GLOBALS

intents = discord.Intents.all()
bot = commands.Bot(intents=intents, command_prefix='!')
bot.remove_command('help')
gh_client: GH_Client
oai_client: OPENAI_Client
cf_client = CF_Client()
server: discord.Guild

notif_channel: discord.TextChannel
debug_channel: discord.TextChannel
command_channels: set[discord.TextChannel]
ressources_channel: discord.TextChannel

member_role: discord.Role
admin_role: discord.Role
bureau_role: discord.Role
event_role: discord.Role

events: set[Event] = set()
reminders: PQ[Reminder] = PQ()
cur_rem: asyncio.Task[None] | None = None

File = open("fixed_data/help.txt")
help_txt = File.read()
File.close()
File = open("fixed_data/admin_help.txt")
admin_help_txt = File.read()
File.close()

fact = 1


#=================================================================================================================================================================
# FUNCTIONS

def update_events() -> int :
    global events
    prev_N = len(events)

    err_code, CF_events = cf_client.get_fut_cont_events()
    if err_code == 1 :
        print(CF_events)
    
    else :
        events |= CF_events

    return len(events) - prev_N

async def connect_gh_client() :
    """
    Connects to the github API
    """
    global gh_client
    try :
        gh_client = GH_Client(sol_token)
    except TokenError as tkerr:
        await debug_channel.send("The github token is wrong or has expired, please generate a new one. See README for more info.")
        raise TokenError from tkerr
    except Exception as err :
        await debug_channel.send(err)
        raise Exception from err

async def connect_openai_client() :
    """
    Connects to the Open AI API
    """
    global oai_client
    try :
        oai_client = OPENAI_Client(openai_token)
    except TokenError as tkerr:
        await debug_channel.send("The github token is wrong or has expired, please generate a new one. See README for more info.")
        raise TokenError from tkerr
    except Exception as err :
        await debug_channel.send(err)
        raise Exception from err

async def wait_reminder() :
    """
    Waits for reminders in the background of the bot
    """
    global reminders

    time = (reminders.queue[0].time - datetime.now()).total_seconds()
    print("waiting for a reminder...")
    await asyncio.sleep(time)
    await notif_channel.send(event_role.mention)
    await notif_channel.send(embed=reminders.get().embed())

    # Loops to wait for the next reminder
    global cur_rem
    if reminders.empty() :
        cur_rem = None
    else :
        cur_rem = asyncio.ensure_future(wait_reminder())

async def help_func(auth: discord.Member, channel: discord.TextChannel) :
        if admin_role in auth.roles and channel == debug_channel :
            await debug_channel.send(embed=embed_help("admin_help.txt"))
        else :
            await channel.send(embed=embed_help("help.txt"))


#=================================================================================================================================================================
# ON_READY

@bot.event
async def on_ready() :
    """
    Executes necessary setup on bot startup
    """
    global events
    events = load_events()

    global reminders
    reminders = generate_queue(events)

    global server
    server = bot.get_guild(716736874797858957)

    global notif_channel
    notif_channel = server.get_channel(1047462537463091212)
    global debug_channel
    debug_channel = server.get_channel(1048584804301537310)
    global command_channels
    command_channels = {debug_channel, server.get_channel(1051626187421650954)}
    global ressources_channel
    ressources_channel = server.get_channel(762706892652675122)

    global member_role
    member_role = server.get_role(716737589205270559)
    global admin_role
    admin_role = server.get_role(737790034270355488)
    global bureau_role
    bureau_role = server.get_role(716737513535963180)
    global event_role
    event_role = server.get_role(1051629248139505715)

    global cur_rem
    if cur_rem is not None :
        cur_rem.cancel()
    if reminders.empty() :
        cur_rem = None
    else :
        cur_rem = asyncio.ensure_future(wait_reminder())

    await connect_gh_client()
    err_code, msg = gh_client.reload_repo_tree()
    if err_code > 0 :
        await debug_channel.send(msg)
    
    await debug_channel.send("Up")


#=================================================================================================================================================================
# ON_MEMBER_JOIN

@bot.event
async def on_member_join(member: discord.Member) :
    """
    Automatically gives member role to newcommers
    """
    await member.add_roles(member_role)


#=================================================================================================================================================================
# ON_MESSAGE

@bot.event
async def on_message(message: discord.Message) :
    """
    Executes commands depending on message received (without command prefix)
    """
    global fact

    # Silly recursive function
    if re.fullmatch("^factorial [0-9]+$", message.content) is not None :
        if message.channel not in command_channels :
            return

        nb = int(message.content.split(' ')[-1])
        if nb < 0 :
            await message.channel.send("number cannot be negative !")
        elif nb > 20 :
            await message.channel.send(f"factorial {nb-1}\njust joking, I'm not doing that")
        elif nb <= 1 :
            await message.channel.send(f"result : {fact}")
            fact = 1
        else :
            fact *= nb
            await asyncio.sleep(1)
            await message.channel.send(f"factorial {nb-1}")
        return

    # Avoid answering itself
    if message.author == bot.user :
        return

    # Help message :
    if message.content.lower() == "help me dijkstra-chan!" :
        await help_func(message.author, message.channel)
        return
    
    # (admin) Command to get README of a repo :
    elif message.content.startswith("embed course ") :
        if admin_role not in message.author.roles :
            return
        
        repo = message.content.split(' ')[2]
        course = ' '.join(message.content.split(' ')[3:])
        err_code, res = gh_client.get_readme(repo, course)

        if err_code == 0 :
            emb = embed(res).set_thumbnail(url="attachment://INSAlgo.png")
            logo = discord.File("fixed_data/INSAlgo.png", filename="INSAlgo.png")
            await ressources_channel.send(file=logo, embed=emb)
        else :
            await debug_channel.send(res)

    # Di-/Cri- words silly answer
    elif "di" in message.content or "cri" in message.content :
        words = message.content.split()
        for i in range(len(words)) :
            if words[i].lower().startswith("di") and len(words[i]) > 2 :
                await message.channel.send(words[i][2:])
                break
            
            if words[i].lower().startswith("cri") and len(words[i]) > 3 :
                await message.channel.send(words[i][3:].upper())
                break
    
    await bot.process_commands(message)


#=================================================================================================================================================================
# EVT COMMAND

@bot.command()
async def evt(ctx: commands.Context, func: str = "get", *args: str) :
    """
    General command prefix for any event related command
    """
    global events
    global reminders
    global cur_rem
    n_args = len(args)
    
    # Command to get/remove the role for events pings :
    if func == "toggle" :
        if ctx.channel not in command_channels :
            return

        if n_args > 0 :
            await ctx.channel.send("toggle does not have parameters")

        msg = "Role successfully "
        if event_role in ctx.author.roles :
            await ctx.author.remove_roles(event_role)
            msg += "removed."
        else :
            await ctx.author.add_roles(event_role)
            msg += "given."
        await ctx.channel.send(msg)

    # Command to display events :
    elif func == "get" :
        if ctx.channel not in command_channels :
            return
        
        if n_args == 0 :
            nb = 3
        elif n_args == 1 :
            nb = int(args[0])
        else :
            nb = int(args[0])
            await ctx.channel.send("get has at most 1 parameter : the number of events to show")
        
        events = remove_passed_events(events)
        list_events = list(events)
        list_events.sort()

        for event in list_events[:nb] :
            await ctx.channel.send(embed=event.embed())
    
    # (admin) Command to update the list events :
    elif func == "update" :
        if admin_role not in ctx.author.roles or ctx.channel != debug_channel :
            return

        if n_args > 0 :
            await ctx.channel.send("update does not have parameters")

        events = remove_passed_events(events)
        N = update_events()
        await ctx.channel.send(f"{N} new event(s) found!")
        save_events(events)

        if N > 0 :
            reminders = generate_queue(events)

            if cur_rem is not None :
                cur_rem.cancel()
            if reminders.empty() :
                cur_rem = None
            else :
                cur_rem = asyncio.ensure_future(wait_reminder())
    
    # (admin) Command to add an event :
    elif func == "add" :
        if admin_role not in ctx.author.roles or ctx.channel != debug_channel :
            return

        event = msg_to_event(ctx.message.content)

        if event is None :
            await ctx.channel.send("please format the date as YYYY/MM/DD HH:MM")

        else :
            events.add(event)
            await ctx.channel.send(f"event {event.name} succesfully added to the list!")
            reminders = generate_queue(events)
            await ctx.channel.send("succesfully generated new reminders!")
            save_events(events)

            if cur_rem is not None :
                cur_rem.cancel()
            if reminders.empty() :
                cur_rem = None
            else :
                cur_rem = asyncio.ensure_future(wait_reminder())


#=================================================================================================================================================================
# SOL(utions) COMMAND

@bot.command()
async def sol(ctx: commands.Context, func: str = "get", *args: str) :
    """
    General command prefix for any solution related command
    """
    n_args = len(args)

    # Command to get the solution of an exercise from a website :
    if func == "get" :
        if ctx.guild and (ctx.channel not in command_channels) :
            return
        
        if n_args == 0 :
            site = ""
            file = ""
        elif n_args == 1 :
            site = args[0]
            file = ""
        else :
            site = args[0]
            file = ' '.join(args[1:])

        _, raw_message = gh_client.search_correction(site, file)
        await ctx.channel.send(raw_message)
    
    # (admin) Command to reload the cache of the Corrections repo tree :
    elif func == "tree" :
        if admin_role not in ctx.author.roles :
            return
        
        if n_args > 0 :
            await ctx.channel.send("tree command does not have parameters")

        _, msg = gh_client.reload_repo_tree()
        await ctx.channel.send(msg)
    
    # (bureau) Command to change the token to access the Corrections repo :
    elif func == "token" :
        if bureau_role not in ctx.author.roles or ctx.channel != debug_channel :
            return
        
        if n_args != 1 :
            await ctx.channel.send("token command has exactly one parameter : the new token")
            return

        global sol_token
        sol_token = args[0]
        await connect_gh_client()


#=================================================================================================================================================================
# G(eometry) COMMAND 

@bot.command()
async def g(ctx: commands.Context, course: str = "", *args: str) :
    """
    General command prefix for any geometry related command
    """
    courses = {"CH"}
    n_args = len(args)
    
    if ctx.channel not in command_channels :
        return

    if course not in courses :
        await ctx.channel.send(f"No command named '{course}'. Available commands are : {', '.join(courses)}.")

    if course == "CH" :
        if n_args == 0 :
            await ctx.channel.send("Type of input to specify : points or polygon.")
            return
        if n_args > 1 :
            await ctx.channel.send("Only one argument required.")
        
        type_ = args[0]
        if type_ == "help" :
            await ctx.channel.send(embed=embed_help("CH_help.txt"))
            return
        if type_ not in {"points", "polygon"} :
            await ctx.channel.send(f"Type of input cannot be '{type_}'. Available types are 'points' and 'polygon'.")
            return

        files = ctx.message.attachments
        if not files:
            await ctx.channel.send("Missing attachment. :poop:")
            return
        attached_file_url = files[0].url
        raw_submission = rqget(attached_file_url).text

        err_code, res = draw_submission(raw_submission, type_)

        if err_code > 1 :
            await ctx.channel.send(res)
            return
        
        message = check(*res, type_)
        await ctx.channel.send(message, file=discord.File("temp.png"))
        return


#=================================================================================================================================================================
# P4 (connect 4) COMMAND

@bot.command()
async def p4(ctx: commands.Context, *args: str) :
    n_args = len(args)

    if n_args == 0 :
        ctx.channel.send("Missing argument")
        return
    
    if args[0] == "help" :
        await ctx.channel.send(embed=embed_help("p4_help.txt"))
        return
    
    if args[0] == "submit" :

        if ctx.guild :
            await ctx.channel.send("You need to send this as a DM :wink:")
            return

        files = ctx.message.attachments
        if not files:
            await ctx.channel.send("Missing attachment. :poop:")
            return
        attached_file_url = files[0].url
        raw_submission = rqget(attached_file_url).text

        ext = files[0].filename.split('.')[-1]
        name = ctx.message.author.name + '.' + ext

        replace = True

        if not os.path.exists("C4_AIs/") :
            os.mkdir("C4_AIs")

        if os.path.exists(f"C4_AIs/{name}") :
            await ctx.channel.send("You already have a submission, do you want to replace it? (Y/N)")

            while True :
                resp: discord.Message = await bot.wait_for("message", check=lambda m: m.channel == ctx.channel)
                if resp.content.upper()[0] == "Y" :
                    replace = True
                    break
                elif resp.content.upper()[0] == "N" :
                    replace = False
                    break
            
        if replace :
            File = open(f"C4_AIs/{name}", 'w')
            File.write(raw_submission)
            File.close()

            await ctx.channel.send("AI submitted ! <:feelsgood:737960024390762568>")
        
        else :
            await ctx.channel.send("Okie Dokie !")


#=================================================================================================================================================================
# HELP COMMAND

@bot.command()
async def help(ctx: commands.Context) :
    await help_func(ctx.author, ctx.channel)


#=================================================================================================================================================================
# SHUTDOWN COMMAND

@bot.command()
@commands.is_owner()
async def shutdown(ctx: commands.Context) :
    if ctx.channel != debug_channel or admin_role not in ctx.author.roles :
        return
    
    await debug_channel.send("shutting down...")
    await bot.close()


#=================================================================================================================================================================
# MAIN "LOOP"

if __name__ == "__main__" :

    # Grabing tokens from environment
    token = os.environ["TOKEN"]
    sol_token = os.environ["GH_TOKEN"]
    openai_token = os.environ["OPENAI_TOKEN"]

    # Running bot
    bot.run(token)

    # Saving stuff after closing
    print("Saving events, DO NOT CLOSE APP!")
    save_events(events)
    os.environ["GH_TOKEN"] = sol_token
    print("saved", len(events), "events to json.")

    # Sending a message to confirm shutdown :
    headers = {'Authorization': 'Bot %s' % token }
    post(f"https://discord.com/api/v6/channels/1048584804301537310/messages", headers=headers, json={"content": "Down"})