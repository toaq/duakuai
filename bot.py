import os
import discord
from dotenv import load_dotenv
import re
import duakuai as dk

COMMAND_PROMPT = re.compile("^:.*")

# setup

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client()

# events

@client.event
async def on_ready():
    for guild in client.guilds:
        print(f'Coechu {client.user} {guild}')

@client.event
async def on_message(msg):
    if COMMAND_PROMPT.match(msg.content):
        response = dk.main(msg.content)
        await msg.channel.send(response)
        



# run client
client.run(TOKEN)
