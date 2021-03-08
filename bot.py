import json
import discord
import requests

from discord import Embed
from discord.ext import tasks
from modules.KillBot import KillBot

client = discord.Client()

@tasks.loop(seconds=30)
async def FetchData(limit=51, offset=0):
    global killbot
    response = requests.get(f'https://gameinfo.albiononline.com/api/gameinfo/events?limit={limit}&offset={offset}')
    DataResponse = response.json()

    requiredData = killbot.SpeedRunData(DataResponse)

    relatedKills = []
    for datum in requiredData:
        killDataExport, parseStatus = killbot.ParseKill(datum)
        if not killDataExport in killbot.PostedKills:
            print (f"[KILL] {killDataExport['killer']} killed {killDataExport['victim']}")
            embeds = killbot.EmbedKill(killDataExport)

            SendKillEmbeds(embeds)

            killbot.PostedKills.append(killDataExport)

        if len(killbot.PostedKills) >= 10:
            killbot.PostedKills = killbot.PostedKills[7:]

    ## Remove images saved locally if a certain size limit is reached.
    killbot.ReduceSpaceUsed()
    
    if len(killbot.KillImagesIDs) > 20:
        killbot.imageManipulator.DeleteImages(killbot.KillImagesIDs)
    
    return None


async def SendKillEmbeds(embeds: list):
    global discord_channel
    for embed_ in embeds:
        await discord_channel.send(embed=embed)

@client.event
async def on_message(message):
    global killbot
    if message.author == client.user:
        return

    if message.content.startswith('$kb_sample'):
        data = killbot.GetSampleData()

        KillDataExport, parseStatus = killbot.ParseKill(data)
        embeds = killbot.EmbedKill(KillDataExport)

        for embed in embeds:
            await message.channel.send(embed=embed)

    if message.content.startswith('$kb_sample_debug'):
        data = killbot.GetSampleData()
        KillDataExport, parseStatus = killbot.ParseKill(data)
        print (KillDataExport)

        embeds = killbot.EmbedKill(KillDataExport)

        for embed in embeds:
            await message.channel.send(embed=embed)


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    FetchData.start()

if __name__ == "__main__":
    with open ('config.json', 'r') as fp:
        config_data = json.load(fp)

    requiredAlliances = [val.strip().lower() for val in config_data['albion_alliances']]
    requiredGuilds = [val.strip().lower() for val in config_data['albion_guilds']]
    requiredPlayers = [val.strip().lower() for val in config_data['albion_players']]


    killbot = KillBot(
        config_data['cloudinary_cloud_name'], 
        config_data['cloudinary_api_key'], 
        config_data['cloudinary_api_secret'], 
        
        requiredAlliances=requiredAlliances,
        requiredGuilds=requiredGuilds,
        requiredPlayers=requiredPlayers
        )

    discord_channel = config_data['discord_channel']
    discord_TOKEN = config_data['discord_token']

    client.run(discord_TOKEN)