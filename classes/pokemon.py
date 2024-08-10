from typing import List, Dict
import requests
import asyncio
from rich import print
from utils.helpers import get_pokemon_info, get_types, get_move_details


class Pokemon:
    """
    "ident": "p1: Snorlax",
    "details": "Snorlax, L84, M",
    "condition": "406/406",
    "active": false,
    "stats": { "atk": 233, "def": 157, "spa": 157, "spd": 233, "spe": 99 },
    "moves": ["crunch", "curse", "return102", "earthquake"],
    "baseAbility": "thickfat",
    "item": "leftovers",
    "pokeball": "pokeball",
    "ability": "thickfat"
    """

    def __init__(
        self,
        ident: str,
        details: str,
        condition: str,
        active: bool,
        stats: Dict,
        moves: List[str],
        item: str,
        ability: str,
    ):
        self.ident = ident
        self.details = details
        self.condition = condition
        self.active = active
        self.stats = stats
        self.item = item
        self.ability = ability

        move_list = []
        for move in moves:
            move_data = get_move_details(move)
            move_list.append({"name": move_data["name"], "type": move_data["type"]})    

        self.moves = move_list

        detail_arr = details.split(",")
        self.name = detail_arr[0].strip()
        self.types: List[str] = get_types(self.name, self.ident[4:])

    def get_ability_info(self):
        url = f"https://pokeapi.co/api/v2/pokemon/{self.name.lower()}"
        print(f"[bold purple]Sending request: {url}[/bold purple]")
        resp_json = requests.get(url).json()

        for pokemon_ability in resp_json["abilities"]:
            if pokemon_ability["ability"]["name"] == self.ability.lower():
                ability_data = requests.get(pokemon_ability["ability"]["url"]).json()
                for effect in ability_data["effect_entries"]:
                    if effect["language"]["name"] == "en":
                        return effect["effect"]

        return "Could not find ability details"

    def get_pokemon_type(self, name: str) -> str:
        url = f"https://pokeapi.co/api/v2/pokemon/{name}"
        print(f"[bold purple]Sending request: {url}[/bold purple]")
        resp_json = requests.get(url).json()
        types = []
        for type_data in resp_json["types"]:
            types.append(type_data["type"]["name"])

        return str(types)

    def __str__(self):
        formatted_moves = ", ".join(f"{move['name']} ({move['type']})" for move in self.moves)
        
        return (
            f"Name: {self.name}\n"
            f"ID: {self.ident}\n"
            f"Details: {self.details}\n"
            f"Condition: {self.condition}\n"
            f"Stats: {self.stats}\n"
            f"Moves: {formatted_moves}\n"
            f"Item: {self.item}\n"
            f"Ability: {self.ability}\n"
            f"Type: {', '.join(self.types)}"
        )