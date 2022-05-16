# IMPORTS
from util.RiotApiMethods import RiotApiMethods
from dotenv import load_dotenv
from discord.ext import commands, tasks
from util.Dotdict import Dotdict
import os
import discord
import json

# CONSTANTS
load_dotenv()
BOT = commands.Bot(command_prefix='!')
TOKEN = os.getenv('TOKEN')
DISCORD_GUILD = os.getenv('DISCORD_GUILD')
API_KEY = os.getenv('API_KEY')
PLATFORM_ROUTING = os.getenv('PLATFORM_ROUTING')
REGIONAL_ROUTING = os.getenv('REGIONAL_ROUTING')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
API = RiotApiMethods(API_KEY, PLATFORM_ROUTING, REGIONAL_ROUTING)
LIVE_TICKER = 60
QUEUE_ID_DICT = {4: 'RANKED', 6: 'RANKED', 42: 'RANKED', 420: 'RANKED', 65: 'ARAM',
                 100: 'ARAM', 450: 'ARAM', 0: 'CUSTOM', 440: 'FLEX', 700: 'CLASH'}

# Setup Method
@BOT.event
async def on_ready():
    match_history = load()

    for puuid, matchID in match_history.items():
        match_history[puuid] = API.lastMatchByPuuid(puuid)

    write(match_history)
    await ticker.start()


# Loops every 60 seconds
@tasks.loop(seconds=LIVE_TICKER)
async def ticker():
    await checkNewGames()


# loads data/match_history.json
def load():
    with open('data/match_history.json', 'r') as f:
        return json.load(f)


# safes given file into data/match_history.json
def write(file):
    with open('data/match_history.json', 'w') as f:
        json.dump(file, f, indent=4)


# adds summoners to match-feed
@BOT.command(name='add')
async def addSummoner(ctx, *, summonerName):
    try:
        match_history = load()
        puuid = API.summonerByName(summonerName)['puuid']
        match_history[puuid] = API.lastMatchByPuuid(puuid)
        write(match_history)
        await ctx.send(f'{summonerName} was successfully added to the match feed.')
    except KeyError:
        await ctx.send(f'There is no summoner with the name {summonerName}.')


# removes summoners from match-feed
@BOT.command(name='remove')
async def removeSummoner(ctx, *, summonerName):
    match_history = load()

    try:
        puuid = API.summonerByName(summonerName)['puuid']
    except KeyError:
        puuid = None

    if str(puuid) in match_history:
        del match_history[puuid]
        await ctx.send(f'{summonerName} was successfully removed from the match feed.')
        print(f'{summonerName} was successfully removed from the match feed.')
    else:
        await ctx.send(f'{summonerName} was not found in your match feed.')
        print(f'{summonerName} was not found in your match feed.')

    write(match_history)


# prints out match-feed
@BOT.command(name="list")
async def printMatchHistory(ctx):
    response = ''
    match_history = load()

    for puuid, matchID in match_history.items():
        response += API.summonerByPuuid(puuid)

    message = discord.Embed(title='**Match-Feed List**',
                            description=response[:-2], colour=discord.Colour.purple())

    await ctx.send(embed=message)


# builds custom data dictionary
def lastMatchData(puuid):
    MATCH_ID = API.lastMatchByPuuid(puuid)
    MATCH = API.matchByMatchId(MATCH_ID)
    INDEX = MATCH['metadata']['participants'].index(puuid)
    PLAYER_DATA = MATCH['info']['participants'][INDEX]
    CUSTOM = {}

    WIN_BOOLEAN = PLAYER_DATA['win']
    CUSTOM['win'] = 'lost'
    CUSTOM['color'] = discord.Colour.red()
    if WIN_BOOLEAN:
        CUSTOM['win'] = 'won'
        CUSTOM['color'] = discord.Colour.green()

    QUEUE_ID = MATCH['info']['queueId']
    CUSTOM['queue'] = 'NORMAL'
    if QUEUE_ID in QUEUE_ID_DICT:
        CUSTOM['queue'] = QUEUE_ID_DICT[QUEUE_ID]

    CUSTOM['name'] = API.summonerByPuuid(puuid)['name']
    CUSTOM['champion'] = PLAYER_DATA['championName']
    CUSTOM['duration'] = round(int(MATCH['info']['gameDuration']) / 60, 2)
    CUSTOM['kills'] = PLAYER_DATA['kills']
    CUSTOM['deaths'] = PLAYER_DATA['deaths']
    CUSTOM['assists'] = PLAYER_DATA['assists']
    if CUSTOM['deaths'] == 0:
        CUSTOM['kda'] = CUSTOM['kills'] + CUSTOM['deaths']
    else:
        CUSTOM['kda'] = round((CUSTOM['kills'] + CUSTOM['assists']) / CUSTOM['deaths'], 2)

    if INDEX > 4:
        teamKills = MATCH['info']['teams'][1]['objectives']['champion']['kills']
    else:
        teamKills = MATCH['info']['teams'][0]['objectives']['champion']['kills']

    if teamKills == 0:
        CUSTOM['killParticipation'] = 0
    else:
        CUSTOM['killParticipation'] = round((float(CUSTOM['kills'] + CUSTOM['assists'])) / float(teamKills) * 100)

    CUSTOM['minions'] = PLAYER_DATA['neutralMinionsKilled'] + PLAYER_DATA['totalMinionsKilled']
    CUSTOM['minionsPerMinute'] = round((CUSTOM['minions'] / CUSTOM['duration']), 2)
    CUSTOM['vision'] = PLAYER_DATA['visionScore']
    CUSTOM['visionPerMinute'] = round((CUSTOM['vision'] / CUSTOM['duration']), 2)
    CUSTOM['controlWards'] = PLAYER_DATA['visionWardsBoughtInGame']

    return Dotdict(CUSTOM)


# builds message of custom dictionary
def buildMessage(data):
    MESSAGE = discord.Embed(title=f'**{data.name.upper()}** {data.win} a {data.queue} game on {data.champion}', color=data.color)
    MESSAGE.add_field(name='GAME DURATION', value=f'{int(data.duration)} minutes', inline=False)
    MESSAGE.add_field(name='STATS', value=f'{data.kills} | {data.deaths} | {data.assists} | KDA: {data.kda} | KP: {data.killParticipation}%', inline=False)
    MESSAGE.add_field(name='MINIONS', value=f'{data.minions} | Minions per minute: {data.minionsPerMinute}', inline=False)
    if data.queue != 'ARAM':
        MESSAGE.add_field(name='VISION SCORE', value=f'{data.vision} | vision per minute: {data.visionPerMinute} | control wards: {data.controlWards}', inline=False)

    return MESSAGE


# checks for new games in match-feed
async def checkNewGames():
    match_history = load()

    for puuid, matchID in match_history.items():
        if matchID != API.lastMatchByPuuid(puuid):
            try:
                DATA = lastMatchData(puuid)
                MESSAGE = buildMessage(DATA)
                await BOT.get_channel(CHANNEL_ID).send(embed=MESSAGE)
            except Exception as e:
                print(e)
            match_history[puuid] = API.lastMatchByPuuid(puuid)

    write(match_history)


# prints out game information
@BOT.command(name="game")
async def game(ctx, *, summonerName):
    puuid = API.summonerByName(summonerName)['puuid']
    try:
        DATA = lastMatchData(puuid)
        MESSAGE = buildMessage(DATA)
        await ctx.send(embed=MESSAGE)
    except Exception as e:
        print(e)
        await ctx.send("Oops! Something went wrong.")


# clears channel
@BOT.command(name='clear')
@commands.has_permissions(administrator=True)
async def clear(ctx, amount=500):
    await ctx.channel.purge(limit=amount)


BOT.run(TOKEN)
