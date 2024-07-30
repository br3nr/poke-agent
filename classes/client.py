import asyncio
import websockets
import requests
import json
import os
import json
import google.generativeai as genai

from typing import List, Dict
from classes.trainer import Trainer
from classes.pokemon import Pokemon


class ShowdownClient:

    def __init__(self, username, password, opponent):
        self.username = username
        self.password = password
        self.opponent = opponent
        self.trainer = None
        self.websocket = None
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash-001", tools=[self.choose_move]
        )

    def choose_move(self, move_name: str):
        """Trigger the next move to be used"""
        move_id = 0
        moves = self.trainer.active_moves
        for i, move in enumerate(moves):
            if move_name == move["move"]:
                move_id = i
        return move_id + 1

    def get_current_moves(self):
        """Gets the available moves for your active pokemon"""
        # TODO: Check move isnt disabled = True
        active_pokemon = self.trainer.get_active_pokemon()
        moves = self.trainer.active_moves
        move_str = ""

        for move in moves:
            move_name = move["move"].lower().replace(" ", "-")
            move_url = f"https://pokeapi.co/api/v2/move/{move_name}"
            try:
                move_data = requests.get(move_url).json()
                for effect in move_data["effect_entries"]:
                    if effect["language"]["name"] == "en":
                        pass
                move_str += f"{move['move']}, "
            except Exception as e:
                pass
        return move_str

    async def battle_loop(self, websocket, message):
        chat = self.model.start_chat(enable_automatic_function_calling=True)
        turn_stats = str(message).split("\n")
        self.battle_id = turn_stats[0][1:]
        if "|request|" in str(message):  # and "active" in str(message):
            # get the player and team data
            try:
                pokemon_stats = turn_stats[1].replace("|request|", "")
                player_dict = json.loads(pokemon_stats)
                if "active" in player_dict:
                    team = self.parse_pokemon(player_dict)
                    self.trainer = Trainer(
                        name=player_dict["side"]["name"],
                        id=player_dict["side"]["id"],
                        team=team,
                        active_moves=player_dict["active"][0]["moves"],
                    )

                elif "forceSwitch" in player_dict:
                    id = self.trainer.get_next_available()
                    if id:
                        payload = f"{self.battle_id}|/choose switch {id}"
                        print(payload)
                        await websocket.send(payload)
            except Exception as e:
                print(e)

        elif "|turn|" in turn_stats[len(turn_stats) - 1]:
            chat = self.model.start_chat(enable_automatic_function_calling=True)
            moves = self.get_current_moves()
            msg = f"""
                You are in a pokemon battle. You must select a move. 
                These are your moves: 
                {moves}

                You may now choose the move. Once you choose the move you will be given its int id. 

                Return the single int id.
            """

            re = chat.send_message(msg).text

            payload = f"{self.battle_id}|/choose move {int(re)}"
            print(payload)
            await self.websocket.send(payload)

    async def get_challenge_data(self, challstr):
        payload = {
            "name": self.username,
            "pass": self.password,
            "challstr": challstr,
        }
        headers = {"User-Agent": "PokeAgentv1"}
        uri = "https://play.pokemonshowdown.com/api/login"
        response = requests.post(uri, data=payload, headers=headers)
        json_str = response.content.decode("utf-8")
        data = json.loads(json_str[1:])
        return data

    async def prompt_and_send_message(self, websocket, msg):
        user_input = input(msg)
        await websocket.send(user_input)

    async def authenticate(self, websocket, message):
        data = await self.get_challenge_data(message[10:])
        assert_str = f"|/trn {self.username},0,{data['assertion']}"
        await websocket.send(assert_str)
        await asyncio.sleep(5)

    def parse_pokemon(self, player_dict: Dict) -> List[Pokemon]:
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

    async def showdown_client(self):
        # Must redefine User-Agent to prevent showdown auto-ban
        # as specified by showdown mods
        headers = {"User-Agent": "PokeAgentv1"}
        url = "wss://sim3.psim.us/showdown/websocket"

        self.websocket = await websockets.connect(url, extra_headers=headers)

        while True:
            # Wait for any incoming message or a timeout
            task = asyncio.wait_for(self.websocket.recv(), timeout=3000)
            message = await task
            print(message)

            if "challstr" in str(message):
                await self.authenticate(self.websocket, message)
                search_battle = f"|/challenge {self.opponent}, gen7randombattle"
                await self.websocket.send(search_battle)
            elif str(message).startswith(">battle"):
                await self.battle_loop(self.websocket, message)
