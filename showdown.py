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
    
    battle_id = None
    turn = 0

    async with websockets.connect(url, extra_headers=headers) as websocket:
        while True:
            # Wait for any incoming message or a timeout
            task = asyncio.wait_for(websocket.recv(), timeout=3000)
            message = await task
             
            print("START\n"+message+"\nEND\n")

            if "challstr" in str(message):
                await authenticate(websocket, message)
                # Uncomment to challenge a user to a battle
                search_battle = "|/challenge br3nr, gen7randombattle"
                await websocket.send(search_battle)
            elif str(message).startswith(">battle"):
                turn_stats = str(message).split("\n") 
                battle_id = turn_stats[0][1:] 
                if str(message[:-1]).endswith("|turn|"):
                    # Do some attack
                    turn += 2
                    #choice = int(input("1) attack 2) swap"))
                    choice = 1
                    if choice == 1:
                        payload = f"{battle_id}|/choose move 1|{turn}"
                        print(payload)
                        await websocket.send(payload)
                elif str(message).endswith("|upkeep"):
                    # Pokemon fainted (either or)
                    turn += 2
                    payload = f"{battle_id}|/choose switch 2|{turn}"
                    print(payload)
                    await websocket.send(payload)

asyncio.run(showdown_client())

