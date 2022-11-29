import discord
 
intents = discord.Intents.all()
client = discord.Client(command_prefix='!', intents=intents)
 
@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
 
@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return
 
    if message.content.startswith('hi'):
        await message.channel.send('Hello!')
 
client.run('MTA0NzIxODUwODc1MDE0MzU3OA.GRYSeJ.wwIuJ3jUk0DSP0Z1K38R1eTtTh14zVxgR7kOhU')