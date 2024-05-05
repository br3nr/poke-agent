import asyncio
import websockets
import requests
import json 

USERNAME = ""
PASSWORD = ""

async def get_challenge_data(challstr):
    payload = {
        "name": USERNAME,
        "pass": PASSWORD,
        "challstr": challstr,
    }

    uri = "https://play.pokemonshowdown.com/api/login"

    response = requests.post(uri, data=payload)
    json_str = response.content.decode('utf-8')  # Decoding the bytes object to a string
    data = json.loads(json_str[1:])
    return data


async def showdown_client():
    url = 'wss://sim3.psim.us/showdown/websocket'
    
    async with websockets.connect(url) as websocket:
        async for message in websocket:
            print(message)
            if ("challstr" in message):
                data = await get_challenge_data(message[10:])
                assert_str = f"|/trn {USERNAME},0,{data['assertion']}" 
                print(assert_str)
                await websocket.send(assert_str)

                search_battle = "|/challenge br3nr, gen7randombattle"
                await websocket.send(search_battle)

if __name__ == "__main__":
    asyncio.run(showdown_client())
