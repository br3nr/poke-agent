import asyncio
import websockets
import requests
import json 
import os 
import time
import re

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


async def prompt_and_send_message(websocket, msg):
    user_input = input(msg)
    await websocket.send(user_input)

async def authenticate(websocket, message):
    data = await get_challenge_data(message[10:])
    assert_str = f"|/trn {USERNAME},0,{data['assertion']}"
    await websocket.send(assert_str)
    await asyncio.sleep(5)

async def showdown_client():
    headers = {
        'User-Agent': 'PokeAgentv1'
    }
    url = 'wss://sim3.psim.us/showdown/websocket'
    
    battle_mode = False
    battle_id = None

    async with websockets.connect(url, extra_headers=headers) as websocket:
        while True:
            try:
                # Wait for any incoming message or a timeout
                task = asyncio.wait_for(websocket.recv(), timeout=30)
                message = await task
                print(message)
                if "challstr" in message:
                    await authenticate(websocket, message)
                    # Uncomment to challenge a user to a battle
                    search_battle = "|/challenge br3nr, gen7randombattle"
                    await websocket.send(search_battle)
                elif message.startswith(">battle"):
                    battle_mode = True
                    print("the message:", message[1:])
                    m = re.search(r'\d+$', str(message[1:]))
                    if m:
                        print(m.group(0))
                elif battle_mode:
                    print("battlemode on:", battle_id)
                elif "|turn|" in message:
                    await prompt_and_send_message(websocket, "Your move")
                elif "error" in message:
                    await prompt_and_send_message(websocket, "try again:")
            except asyncio.TimeoutError:
                # Handle the case where no message is received in 10 seconds
                await prompt_and_send_message(websocket, "Timeout")

asyncio.run(showdown_client())

