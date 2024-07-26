import asyncio
import websockets
import requests
import json
import os
import json

from typing import List, Dict
from classes.pokemon import Pokemon
from classes.trainer import Trainer

from dotenv import load_dotenv

load_dotenv()

USERNAME = os.environ.get("SHOWDOWN_USERNAME")
PASSWORD = os.environ.get("SHOWDOWN_PASSWORD")
OPPONENT = "br3nr"


async def get_challenge_data(challstr):
    payload = {
        "name": USERNAME,
        "pass": PASSWORD,
        "challstr": challstr,
    }
    headers = {"User-Agent": "PokeAgentv1"}
    uri = "https://play.pokemonshowdown.com/api/login"
    response = requests.post(uri, data=payload, headers=headers)
    json_str = response.content.decode("utf-8")
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


def parse_pokemon(player_dict: Dict) -> List[Pokemon]:
    pokemon_data = player_dict["side"]["pokemon"]
    team = []
    for pokemon_dict in pokemon_data:
        team.append(
            Pokemon(
                ident=pokemon_dict["ident"],
                details=pokemon_dict["details"],
                condition=pokemon_dict["condition"],
                active=pokemon_dict["active"],
                stats=pokemon_dict["stats"],
                moves=pokemon_dict["moves"],
                item=pokemon_dict["item"],
                ability=pokemon_dict["ability"],
            )
        )
    return team


async def showdown_client():
    # Must redefine User-Agent to prevent showdown auto-ban
    # as specified by showdown mods
    headers = {"User-Agent": "PokeAgentv1"}
    url = "wss://sim3.psim.us/showdown/websocket"

    battle_id = None
    turn = 0
    trainer = None

    async with websockets.connect(url, extra_headers=headers) as websocket:
        while True:
            # Wait for any incoming message or a timeout
            task = asyncio.wait_for(websocket.recv(), timeout=3000)
            message = await task
            print(message)

            if "challstr" in str(message):
                await authenticate(websocket, message)
                search_battle = f"|/challenge {OPPONENT}, gen7randombattle"
                await websocket.send(search_battle)
            elif str(message).startswith(">battle"):
                turn_stats = str(message).split("\n")
                battle_id = turn_stats[0][1:]
                if str(message[:-1]).endswith("|turn|"):
                    # Do some attack
                    turn += 2
                    payload = f"{battle_id}|/choose move 1|{turn}"
                    print(payload)
                    await websocket.send(payload)
                elif str(message).endswith("|upkeep"):
                    # p1 or p2 pokemon fainted
                    # TODO: refine detection
                    turn += 2
                    payload = f"{battle_id}|/choose switch 2|{turn}"
                    await websocket.send(payload)
                elif "|request|" in str(message) and "active" in str(message):
                    # get the player and team data
                    pokemon_stats = turn_stats[1].replace("|request|", "")
                    player_dict = json.loads(pokemon_stats)
                    team = parse_pokemon(player_dict)
                    trainer = Trainer(
                        name=player_dict["side"]["name"],
                        id=player_dict["side"]["id"],
                        team=team,
                    )


asyncio.run(showdown_client())
