from discord.ext.commands import Context, command, Bot

from bot import bot

from functions.events import events, remove_passed_events, update_events, save_events, generate_queue, launch_reminder, msg_to_event

# Command function :

@command()
async def evt(ctx: Context, func: str = "get", *args: str) :
    n_args = len(args)
    
    # Command to get/remove the role for events pings :
    if func == "toggle" :
        if ctx.channel not in {bot.channels["debug"], bot.channels["command"]} :
            return

        if n_args > 0 :
            await ctx.channel.send("toggle does not have parameters")

        msg = "Role successfully "
        if bot.roles["event"] in ctx.author.roles :
            await ctx.author.remove_roles(bot.roles["event"])
            msg += "removed."
        else :
            await ctx.author.add_roles(bot.roles["event"])
            msg += "given."
        await ctx.channel.send(msg)

    # Command to display events :
    elif func == "get" :
        if ctx.channel not in {bot.channels["debug"], bot.channels["command"]} :
            return
        
        if n_args == 0 :
            nb = 3
        elif n_args == 1 :
            nb = int(args[0])
        else :
            nb = int(args[0])
            await ctx.channel.send("get has at most 1 parameter : the number of events to show")
        
        remove_passed_events()
        list_events = list(events)
        list_events.sort()

        for event in list_events[:nb] :
            await ctx.channel.send(embed=event.embed())
    
    # (admin) Command to update the list events :
    elif func == "update" :
        if bot.roles["admin"] not in ctx.author.roles or ctx.channel != bot.channels["debug"] :
            return

        if n_args > 0 :
            await ctx.channel.send("`!evt update` does not have parameters")

        remove_passed_events()
        N = update_events()
        await ctx.channel.send(f"{N} new event(s) found!")
        save_events()

        if N > 0 :
            generate_queue(events)

            launch_reminder()
    
    # (admin) Command to add an event :
    elif func == "add" :
        if bot.roles["admin"] not in ctx.author.roles or ctx.channel != bot.channels["debug"] :
            return

        event = msg_to_event(ctx.message.content)

        if event is None :
            await ctx.channel.send("please format the date as YYYY/MM/DD HH:MM")

        else :
            events.add(event)
            await ctx.channel.send(f"event {event.name} succesfully added to the list!")
            generate_queue()
            await ctx.channel.send("succesfully generated new reminders!")
            save_events()

            launch_reminder()


# Required setup :

async def setup(bot: Bot) :
    bot.add_command(evt)