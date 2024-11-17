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
from classes.api import DexAPI

from utils.config import safety_filters
from utils.helpers import (
    get_challenge_data,
    get_types,
    get_pokemon_info,
    get_damage_relations,
    print_agent_function_call
)


class ShowdownClient:

    def __init__(self, username, password, opponent_name):
        self.username = username
        self.password = password
        self.opponent_name = opponent_name
        self.trainer = None
        self.opponent = Opponent(pid="p2a")
        self.websocket = None
        self.move_queue: List[str] = []
        self.battle_log: List[str] = []

    # Tool
    def choose_move(self, move_name: str):
        """Trigger the next move to be used"""
        print_agent_function_call("choose_move", move_name)
        move_id = 0
        moves = self.trainer.active_moves
        for i, move in enumerate(moves):
            if move_name == move["move"]:
                move_id = i

        payload = f"{self.battle_id}|/choose move {move_id+1}"
        print("p:", payload)
        self.move_queue.append(payload)

    def swap_pokemon(self, pokemon_name: str):
        """Swap your current pokemon for a pokemon in your team"""
        print_agent_function_call("swap_pokemon", pokemon_name)
        pokemon_id = self.trainer.get_pokemon_id(pokemon_name=pokemon_name)
        payload = f"{self.battle_id}|/choose switch {pokemon_id}"
        print("p:", payload)
        self.move_queue.append(payload)

    def check_type_advantages(self, pokemon_name: str) -> str:
        """Takes the name of a pokemon. Returns the what types the pokemon is good and bad against."""
        types = get_types(pokemon_name=pokemon_name)
        relations =  get_damage_relations(types)
        response = f"Here are the resistances, weaknesses and immunities for {pokemon_name}.\nNOTE: Asterisk * represents double factor on the weakness or resistance.\n{relations}"
        print_agent_function_call("check_type_advantages", pokemon_name, relations)
        return relations 

    def get_team_details(self, team_name: str = "team") -> str:
        """Returns a list of types that the provided type is strong and weak against. Pass any variable to use this function."""
        team = self.trainer.get_team()
        team_list = []
        for mon in team:
            if mon.condition != "0 fnt":
                team_list.append({"name": mon.name, "type": mon.types})

        print_agent_function_call("get_team_details", team_name, team_list)
        return str(team_list)

    # Tool
    def get_pokemon_details(self, pokemon_name: str) -> str:
        """Gets the details about one of the pokemon in your team"""
        team = self.trainer.get_team()
        for mon in team:
            #print(mon.name, pokemon_name)
            if mon.name == pokemon_name:
                print_agent_function_call("get_pokemon_details", pokemon_name, mon)
                return str(mon)
        return "Could not find pokemon"

    def get_opponent_pokemon_details(self, pokemon_name: str) -> str:
        """Gets the details about the opponents pokemon"""
        types = get_types(pokemon_name)
        details = f"{pokemon_name} {', '.join(types)} type pokemon."
        print_agent_function_call("get_opponent_pokemon_details", pokemon_name, details)
        return details

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
                    #"description": description,
                }
            )
        return detailed_moves

    def process_battle_log(self, turn_stats):
        for turn in turn_stats:
            if "|switch|p2a:" in turn:
                match = re.search(r"\bp2a: (\w+)", turn)
                if match:
                    pokemon_name = match.group(1)
                    self.opponent.active_pokemon = pokemon_name

    async def battle_loop(self, websocket, message):
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
                        await websocket.send(payload)
            except Exception as e:
                traceback.print_exc()
                pass
        elif "|turn|" in turn_stats[len(turn_stats) - 1]:
            self.process_battle_log(turn_stats)
            self.main_agent_executor() 
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
            if "challstr" in str(message):
                await self.authenticate(self.websocket, message)
                search_battle = f"|/challenge {self.opponent_name}, gen7randombattle"
                await self.websocket.send(search_battle)
            elif str(message).startswith(">battle"):
                await self.battle_loop(self.websocket, message)

    def main_agent_executor(self):

        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash-001",
            #model_name="gemini-1.5-pro",
            tools=[
                self.get_agent_analyis,
                self.choose_move,
                self.swap_pokemon
            ],
            generation_config={"temperature": 0},
            safety_settings=safety_filters,
        )
        
        chat = model.start_chat(enable_automatic_function_calling=True)

        msg = f"""
        
        You are an AI agent part of a larger agentic system. The system is responsible for taking actions in a pokemon battle. 
        Your task in the system is to orchestrate the other agents.
        Once your orchestration is complete, you will execute the next action.
        Your available actions are: 
            1) Change pokemon
            2) Execute move
        """ 
        
        response = None
        while response is None:
            try:
                response = chat.send_message(msg).text
            except ResourceExhausted:
                print("[bold purple]Sleeping...[/bold purple]")
                time.sleep(15)
                        
        print(f"[bold bright_yellow]Orchestrator Agent\n{response}[/bold bright_yellow]")

    def get_agent_analyis(self, value: str = ""):
        """Analyses the current move and suggests the next move to make."""

        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash-001",
            #model_name="gemini-1.5-pro",
            tools=[
                self.get_pokemon_details,
                self.get_opponent_pokemon_details,
                self.get_team_details,
                self.check_type_advantages,
            ],
            generation_config={"temperature": 0},
            safety_settings=safety_filters,
        )

        chat = model.start_chat(enable_automatic_function_calling=True)
        moves = self.get_current_moves()
        active_pokemon = self.trainer.get_active_pokemon().name
        print(moves)
        msg = f"""
            You are an AI agent part of a larger agentic system. The system is responsible for taking actions in a pokemon battle. 
            Your task is to evaluate the current state of the battle and assess what the next action should be. 
            Specifically, you will be looking to see if the next action should be to use a move or switch pokemon.
            In your analysis, you must only use the knowledge available to you in the functions you can call. Do not rely on any pre existing knowledge.
            Your analysis will be past to the next agent in the system, so format your response appropriately. 
            Think carefully and take your time. 

            Here are some considerations:
                1) Is the pokemon you are up against strong against yours, or is it resistent against yours? If so, consider swapping.
                2) Does your pokemon have any super effective moves against the opponent? If so, consider using it. 
                3) Should you use any moves in preparation for a larger follow up move? 
                4) If you decide to swap to another pokemon, you must first check your team composition. 
                5) Check your other team, are there any pokemon that are super effective against your opponent?

            These considerations are simple guidelines, use your best judgement.   

            Your active Pokémon is {active_pokemon}. These are your moves: {moves}

            You are currently facing the opponent’s {self.opponent.active_pokemon}

            Perform your analysis below:
        """ 
        
        response = None
        while response is None:
            try:
                response = chat.send_message(msg).text
            except ResourceExhausted:
                print("[bold purple]Sleeping...[/bold purple]")
                time.sleep(15)
        
        print(f"[bold purple]Analysis Agent\n{response}[/bold purple]")
        return response

