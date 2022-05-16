import requests

class ApiError(Exception): pass

class RiotApiMethods:
    def __init__(self, key='', platformRouting='', regionalRouting=''):
        self.key = key
        self.platformRouting = platformRouting
        self.regionalRouting = regionalRouting

    def summonerByPuuid(self, puuid):
        return getJson(f'https://{self.platformRouting}.api.riotgames.com/lol/summoner/v4/'
                       f'summoners/by-puuid/{puuid}?api_key={self.key}')

    def summonerByName(self, name):
        return getJson(f'https://{self.platformRouting}'f'.api.riotgames.com/lol/summoner/v4/'
                       f'summoners/by-name/{name}?api_key={self.key}')

    def matchListByPuuid(self, puuid, startTime='', endTime='', queue='', typeId='', start='', count=''):
        return getJson(f'https://{self.regionalRouting}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?'
                       f'startTime={startTime}&endTime={endTime}&queue={queue}&type={typeId}&start={start}'
                       f'&count={count}&api_key={self.key}')

    def lastMatchByPuuid(self, puuid):
        return self.matchListByPuuid(puuid)[0]

    def matchByMatchId(self, matchId):
        return getJson(f'https://{self.regionalRouting}.api.riotgames.com/'
                       f'lol/match/v5/matches/{matchId}?api_key={self.key}')


def getJson(url):
    try:
        return requests.get(url).json()
    except Exception:
        raise ApiError



