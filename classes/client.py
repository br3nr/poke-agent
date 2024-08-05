import asyncio
import websockets
import requests
import json
import time
import json
import google.generativeai as genai
import re
import traceback
from google.api_core.exceptions import ResourceExhausted

from rich import print
from typing import List, Dict

from classes.trainer import Trainer
from classes.opponent import Opponent
from classes.pokemon import Pokemon
from utils.config import safety_filters
from utils.helpers import (
    get_challenge_data,
    get_types,
    get_pokemon_info,
    get_damage_relations,
)


class ShowdownClient:

    def __init__(self, username, password, opponent_name):
        self.username = username
        self.password = password
        self.opponent_name = opponent_name
        self.trainer = None
        self.opponent = Opponent(pid="p2a")
        self.websocket = None
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash-001",
            #model_name="gemini-1.5-pro",
            tools=[
                #self.choose_move,
                self.get_pokemon_details,
                self.get_opponent_pokemon_details,
                self.check_type_advantages,
                self.get_team_details,
                #self.swap_pokemon
            ],
            safety_settings=safety_filters,
        )
        self.move_queue: List[str] = []
        self.battle_log: List[str] = []

    # Tool
    def choose_move(self, move_name: str):
        """Trigger the next move to be used"""
        print(
            f"[bold bright_blue]Agent triggered choose_move with input: {move_name}[/bold bright_blue]"
        )

        move_id = 0
        moves = self.trainer.active_moves
        print(moves)
        for i, move in enumerate(moves):
            if move_name == move["move"]:
                move_id = i

        payload = f"{self.battle_id}|/choose move {move_id+1}"
        self.move_queue.append(payload)
        time.sleep(5)

    def swap_pokemon(self, pokemon_name: str):
        """Swap your current pokemon for a pokemon in your team"""
        print(
            f"[bold bright_blue]Agent triggered swap_pokemon with input: {pokemon_name}[/bold bright_blue]"
        )
        pokemon_id = self.trainer.get_pokemon_id(pokemon_name)
        payload = f"{self.battle_id}|/choose switch {pokemon_id}"
        self.move_queue.append(payload)
        time.sleep(5)

    def check_type_advantages(self, pokemon_name: str) -> str:
        """Takes the name of a pokemon. Returns the what types the pokemon is good and bad against."""
        time.sleep(5)
        types = get_types(pokemon_name=pokemon_name)
        relations =  get_damage_relations(types)
        response = f"Here are the resistances, weaknesses and immunities for {pokemon_name}.\nNOTE: Asterisk * represents double factor on the weakness or resistance.\n{relations}"
        print(
            f"[bold bright_blue]Agent triggered get_type_advantages with input: {pokemon_name} returning: {response}[/bold bright_blue]"
        )

        return response 

    def get_team_details(self, team_name: str = "team") -> str:
        """Returns a list of types that the provided type is strong and weak against. Pass any variable to use this function."""
        print(
            f"[bold bright_blue]Agent triggered get_team_details with input: {team_name}[/bold bright_blue]"
        )
        team = self.trainer.get_team()
        team_list = []
        for mon in team:
            if mon.condition != "0 fnt":
                team_list.append(str(mon))

        print(team_list)
        time.sleep(5)
        return str(team_list)

    # Tool
    def get_pokemon_details(self, pokemon_name: str) -> str:
        """Gets the details about one of the pokemon in your team"""
        print(
            f"[bold bright_blue]Agent triggered get_pokemon_details with input: {pokemon_name}[/bold bright_blue]"
        )
        team = self.trainer.get_team()
        for mon in team:
            print(mon.name, pokemon_name)
            if mon.name == pokemon_name:
                print(mon)
                return str(mon)
        time.sleep(5)
        return "Could not find pokemon"

    def get_opponent_pokemon_details(self, pokemon_name: str) -> str:
        """Gets the details about the opponents pokemon"""
        types = get_types(pokemon_name)
        print(
            f"[bold bright_blue]Agent triggered get_opponent_pokemon_details with input: {pokemon_name} and output: {types}[/bold bright_blue]"
        )
        time.sleep(5)
        return f"The opponents {pokemon_name} is the following type: {types}"

    def get_current_moves(self):
        " ""Gets the available moves for your active pokemon"""
        # TODO: Check move isnt disabled = True
        active_pokemon = self.trainer.get_active_pokemon()
        moves = self.trainer.active_moves
        move_str = ""
        detailed_moves = []
        description = ""

        for move in moves:
            move_name_fmt = move["move"].lower().replace(" ", "-")

            if "hidden-power" in move_name_fmt:
                # TODO: Determine better way to handle edge cases
                move_name_fmt = "hidden-power"
            elif "return-102" in move_name_fmt:
                # because it does up to 102, always in showdown 102 
                move_name_fmt = "return"
            
            move_url = f"https://pokeapi.co/api/v2/move/{move_name_fmt}"
            print(f"[bold purple]Sending request: {move_url}[/bold purple]")

            # try
            move_data = requests.get(move_url).json()

            move_name = move["move"]
            damage_type = move_data["type"]["name"]
            damage_class = move_data["damage_class"]["name"]
            accuracy = move_data["accuracy"]
            power = move_data["power"]

            for effect in move_data["effect_entries"]:
                if effect["language"]["name"] == "en":
                    description = effect["effect"]  # short_effect available

            move_str += f"{move['move']}, "

            detailed_moves.append(
                {
                    "name": move_name,
                    "type": damage_type,
                    "class": damage_class,
                    "accuracy": accuracy,
                    "power": power,
                    "description": description,
                }
            )

        return detailed_moves

    def process_battle_log(self, turn_stats):
        for turn in turn_stats:
            if "|switch|p2a:" in turn:
                match = re.search(r"\bp2a: (\w+)", turn)
                if match:
                    pokemon_name = match.1group(1)
                    self.opponent.active_pokemon = pokemon_name

    async def battle_loop(self, websocket, message):
        chat = self.model.start_chat(enable_automatic_function_calling=True)
        turn_stats = str(message).split("\n")
        self.battle_id = turn_stats[0][1:]
        
#        payload = f"{self.battle_id}|/data gliscor"
#        await self.websocket.send(payload)
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
                traceback.print_exc()
                pass
        elif "|turn|" in turn_stats[len(turn_stats) - 1]:
            print(message)

            chat = self.model.start_chat(enable_automatic_function_calling=True)
            moves = self.get_current_moves()

            self.process_battle_log(turn_stats)
            # Run queries on the type of opposing pokemon
            # What type do we have?
            self.get_team_details()

            active_pokemon = self.trainer.get_active_pokemon().name
            print("Opponent pok: ", self.opponent.active_pokemon)

            msg = f"""
                You are a pro Pokémon analyst analyzing the current state of a Pokémon battle on Pokémon Showdown. Your task is to make a detailed analysis and provide a recommendation based on the facts obtained from the functions.

                Your active Pokémon is {active_pokemon}. These are your moves: {moves}

                You are currently facing the opponent’s {self.opponent.active_pokemon}

                Using all functions available to you, perform an analysis of the current game state.
                What is the composition of the team, what is your pokemon resistant/weak too, what is the opponent resistant/weak too. 

                Perform a thorough analysis. Once complete, make a reccomendation on what should be done next.
            """
            
            response = None
            while response is None:
                try:
                    response = chat.send_message(msg).text
                except ResourceExhausted:
                    print("[bold purple]Sleeping...[/bold purple]")
                    time.sleep(5)
                            
            print(f"[bold bright_yellow]{response}[/bold bright_yellow]")
            await self.websocket.send(self.move_queue.pop())

    async def authenticate(self, websocket, message):
        data = get_challenge_data(message[10:], self.username, self.password)
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
                search_battle = f"|/challenge {self.opponent_name}, gen7randombattle"
                await self.websocket.send(search_battle)
            elif str(message).startswith(">battle"):
                await self.battle_loop(self.websocket, message)
