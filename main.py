#=================================================================================================================================================================
# IMPORTS

import os
import asyncio
import re
from requests import post

import discord
from discord.ext.commands import Context

from bot import bot

from extensions.evt.utils   import daily_update, save_events

from utils.embeding import embed_help, embed


#=================================================================================================================================================================
# GLOBALS

File = open("fixed_data/help.txt")
help_txt = File.read()
File.close()
File = open("fixed_data/admin_help.txt")
admin_help_txt = File.read()
File.close()

fact = 1


#=================================================================================================================================================================
# FUNCTION TO SEND HELP

async def help_func(channel) :
        if channel == bot.channels["debug"] :
            await bot.channels["debug"].send(embed=embed_help("admin_help.txt"))
        else :
            await channel.send(embed=embed_help("help.txt"))


#=================================================================================================================================================================
# ON_MEMBER_JOIN

@bot.client.event
async def on_member_join(member: discord.Member) :
    """
    Automatically gives member role to newcommers
    """
    await member.add_roles(bot.roles["member"])


#=================================================================================================================================================================
# ON_REACTION_ADD

@bot.client.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User) :
    # This might be usefull
    pass

#=================================================================================================================================================================
# ON_MESSAGE

@bot.client.event
async def on_message(message: discord.Message) :
    """
    Executes commands depending on message received (without command prefix)
    """
    global fact

    # Silly recursive function
    if re.fullmatch("^factorial [0-9]+$", message.content) is not None :
        if message.channel not in {bot.channels["debug"], bot.channels["command"]} :
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
    if message.author == bot.client.user :
        return

    # Help message :
    if message.content.lower() == "help me dijkstra-chan!" :
        await help_func(message.channel)
        return
    
    # (admin) Command to get README of a repo :
    elif message.content.startswith("embed course ") :
        if bot.roles["admin"] not in message.author.roles :
            return
        
        repo = message.content.split(' ')[2]
        course = ' '.join(message.content.split(' ')[3:])
        err_code, res = bot.client.get_cog("GH_ClientCog").get_readme(repo, course)

        if err_code == 0 :
            emb = embed(res).set_thumbnail(url="attachment://INSAlgo.png")
            logo = discord.File("fixed_data/INSAlgo.png", filename="INSAlgo.png")
            await bot.channels["ressources"].send(file=logo, embed=emb)
        else :
            await bot.channels["debug"].send(res)

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
    
    await bot.client.process_commands(message)


#=================================================================================================================================================================
# HELP COMMAND

@bot.client.command()
async def help(ctx: Context) :
    await help_func(ctx.channel)


#=================================================================================================================================================================
# SHUTDOWN COMMAND

@bot.client.command()
async def shutdown(ctx: Context) :
    if ctx.channel != bot.channels["debug"] or bot.roles["admin"] not in ctx.author.roles :
        return
    
    await bot.channels["debug"].send("shutting down...")
    await bot.client.close()


#=================================================================================================================================================================
# MAIN

from cogs.Github_Client import GH_ClientCog
from cogs.Solutions import SolutionsCog
from cogs.Geometry import GeometryCog

if __name__ == "__main__" :

    # Grabing tokens from environment
    openai_token = os.environ["OPENAI_TOKEN"]

    # Bot commands setup
    bot.define_on_ready([daily_update.start])
    asyncio.run(bot.client.load_extension("extensions.evt.command"))
    asyncio.run(bot.client.load_extension("extensions.game.command"))
    asyncio.run(bot.client.add_cog(GH_ClientCog()))
    asyncio.run(bot.client.add_cog(SolutionsCog(bot.client)))
    asyncio.run(bot.client.add_cog(GeometryCog()))

    bot.run()

    # Saving stuff after closing
    print("Saving events, DO NOT CLOSE APP!")
    save_events()

    # Sending a message to confirm shutdown :
    headers = {'Authorization': 'Bot %s' % bot.token }
    post(f"https://discord.com/api/v6/channels/1048584804301537310/messages", headers=headers, json={"content": "Down"})
