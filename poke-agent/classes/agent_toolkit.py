
from utils.config import safety_filters
import google.generativeai as genai
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
from classes.battle_data import BattleData
from rich import print

from utils.helpers import (
    get_challenge_data,
    get_types,
    get_pokemon_info,
    get_damage_relations,
    print_agent_function_call,
)

class AgentToolkit():
    
    def __init__(self):
        self.battle_data = BattleData()

    def get_pokemon_details(self, pokemon_name: str) -> str:
        """Gets the details about one of the pokemon in your team"""
        team = self.battle_data.trainer.get_team()
        for mon in team:
            # print(mon.name, pokemon_name)
            if mon.name == pokemon_name:
                print_agent_function_call("get_pokemon_details", pokemon_name, mon)
                return str(mon)
        return "Could not find pokemon"

    def get_opponent_pokemon_details(self, pokemon_name: str) -> str:
        """Gets the details about the opponents pokemon"""
        types = get_types(pokemon_name)
        details = f"The opponets {pokemon_name} is a {' and '.join(types)} type pokemon."
        details += f"\n{self.check_type_advantages(pokemon_name)}"
        print_agent_function_call("get_opponent_pokemon_details", pokemon_name, details)
        
        return details


    def get_team_details(self, team_name: str = "team") -> str:
        """Returns all of the pokemon in the team"""
        team = self.battle_data.trainer.get_team()
        team_list = []
        for mon in team:
            if mon.condition != "0 fnt" or mon.name != self.battle_data.trainer.get_active_pokemon().name:
                team_list.append({"name": mon.name, "type": mon.types})
       
        print(str(team_list))
        print_agent_function_call("get_team_details", team_name, team_list)
        return str(team_list)

    def check_type_advantages(self, pokemon_name: str) -> str:
        """Takes the name of a pokemon. Returns the what types the pokemon is good and bad against."""
        types = get_types(pokemon_name=pokemon_name)
        relations = get_damage_relations(types)
        response = f"Here are the resistances, weaknesses and immunities for {pokemon_name}.\nNOTE: Asterisk * represents double factor on the weakness or resistance.\n{relations}"
        print_agent_function_call("check_type_advantages", pokemon_name, relations)
        return relations

    def get_current_moves(self):
        " " "Gets the available moves for your active pokemon" ""
        # TODO: Check move isnt disabled = True
        active_pokemon = self.battle_data.trainer.get_active_pokemon()
        moves = self.battle_data.trainer.active_moves
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
                    # "description": description,
                }
            )
        return detailed_moves
