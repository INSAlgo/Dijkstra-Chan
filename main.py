#=================================================================================================================================================================
# IMPORTS

import os
import asyncio
import re
from requests import get as rqget
from requests import post

import discord
from discord.ext.commands import Context, Bot

from classes.token_error import TokenError
from classes.github_client import GH_Client
from classes.openai_client import OPENAI_Client

from functions.embeding import embed, embed_help

from commands.evt   import command_ as evt_com, save_events, fetch_notif_channel
from commands.sol   import command_ as sol_com
from commands.g     import command_ as g_com


#=================================================================================================================================================================
# GLOBALS

bot = Bot(intents=discord.Intents.all(), command_prefix='!')
bot.remove_command('help')

server: discord.Guild

notif_channel: discord.TextChannel
debug_channel: discord.TextChannel
command_channels: set[discord.TextChannel]
ressources_channel: discord.TextChannel

member_role: discord.Role
admin_role: discord.Role
bureau_role: discord.Role
event_role: discord.Role

gh_client: GH_Client
oai_client: OPENAI_Client

File = open("fixed_data/help.txt")
help_txt = File.read()
File.close()
File = open("fixed_data/admin_help.txt")
admin_help_txt = File.read()
File.close()

fact = 1


#=================================================================================================================================================================
# CLIENTS CONNECTION FUNCTIONS

async def connect_gh_client(token) :
    """
    Connects to the github API
    """
    global gh_client
    try :
        gh_client = GH_Client(token)
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


#=================================================================================================================================================================
# FUNCTION TO SEND HELP

async def help_func(auth: discord.Member, channel: discord.TextChannel) :
        if channel == debug_channel :
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

    fetch_notif_channel(notif_channel)

    await connect_gh_client(os.environ["GH_TOKEN"])
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
# ON_REACTION_ADD

@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User) :
    # This might be usefull
    pass

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
async def evt(ctx: Context, func: str = "get", *args: str) :
    """
    General command prefix for any event related command
    """
    await evt_com(
        admin_role, event_role,
        debug_channel, command_channels,
        ctx, func, *args
    )   # Using keywords arguments (like ctx = ctx) breaks everything for some reason


#=================================================================================================================================================================
# SOL(utions) COMMAND

@bot.command()
async def sol(ctx: Context, func: str = None, *args: str) :
    """
    General command prefix for any solution related command
    """
    new_token = await sol_com(
        gh_client,
        admin_role, event_role,
        debug_channel, command_channels,
        ctx, func, *args
    )

    if new_token is not None :
        connect_gh_client(new_token)


#=================================================================================================================================================================
# G(eometry) COMMAND 

@bot.command()
async def g(ctx: Context, course: str = "", *args: str) :
    """
    General command prefix for any geometry related command
    """
    await g_com(command_channels, ctx, course, *args)


#=================================================================================================================================================================
# P4 (connect 4) COMMAND

@bot.command()
async def p4(ctx: Context, *args: str) :
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
async def help(ctx: Context) :
    await help_func(ctx.author, ctx.channel)


#=================================================================================================================================================================
# SHUTDOWN COMMAND

@bot.command()
async def shutdown(ctx: Context) :
    if ctx.channel != debug_channel or admin_role not in ctx.author.roles :
        return
    
    await debug_channel.send("shutting down...")
    await bot.close()


#=================================================================================================================================================================
# MAIN "LOOP"

if __name__ == "__main__" :

    # Grabing tokens from environment
    token = os.environ["TOKEN"]
    openai_token = os.environ["OPENAI_TOKEN"]

    # Running bot
    bot.run(token)

    # Saving stuff after closing
    print("Saving events, DO NOT CLOSE APP!")
    save_events()

    # Sending a message to confirm shutdown :
    headers = {'Authorization': 'Bot %s' % token }
    post(f"https://discord.com/api/v6/channels/1048584804301537310/messages", headers=headers, json={"content": "Down"})