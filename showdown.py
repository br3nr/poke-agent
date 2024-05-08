import asyncio
import websockets
import requests
import json 
import os 

from dotenv import load_dotenv
load_dotenv()

USERNAME = os.environ.get("SHOWDOWN_USERNAME")
PASSWORD = os.environ.get("SHOWDOWN_PASSWORD")

async def get_challenge_data(challstr):
    payload = {
        "name": USERNAME,
        "pass": PASSWORD,
        "challstr": challstr,
    }
    headers = {
        'User-Agent': 'PokeAgentv1'
    }
    uri = "https://play.pokemonshowdown.com/api/login"
    response = requests.post(uri, data=payload, headers=headers)
    json_str = response.content.decode('utf-8')
    data = json.loads(json_str[1:])
    return data

async def showdown_client():
    headers = {
        'User-Agent': 'PokeAgentv1'
    }
    url = 'wss://sim3.psim.us/showdown/websocket'
    async with websockets.connect(url, extra_headers=headers) as websocket:
        async for message in websocket:
            print(message)
            if "challstr" in message:
                data = await get_challenge_data(message[10:])
                assert_str = f"|/trn {USERNAME},0,{data['assertion']}" 
                print(assert_str)
                await websocket.send(assert_str)
                # Uncomment to challenge a user to a battle
                search_battle = "|/challenge br3nr, gen7randombattle"
                await websocket.send(search_battle)

if __name__ == "__main__":
    asyncio.run(showdown_client())

