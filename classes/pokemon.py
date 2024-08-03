from typing import List, Dict 
import requests
import asyncio


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
        self.moves = moves
        self.item = item
        self.ability = ability
    
        detail_arr = details.split(",")
        self.name = detail_arr[0].strip()

    
    def get_ability_info(self):
        print(f"https://pokeapi.co/api/v2/pokemon/{self.name.lower()}")
        resp_json = requests.get(f"https://pokeapi.co/api/v2/pokemon/{self.name.lower()}").json()
        print(self.name, self.ability) 
        for pokemon_ability in resp_json["abilities"]:
            if pokemon_ability["ability"]["name"] == self.ability.lower():
                ability_data = requests.get(pokemon_ability["ability"]["url"]).json()
                for effect in ability_data["effect_entries"]:
                    if effect["language"]["name"] == "en":
                        return effect["effect"]

        return "Could not find ability details"
          

    def get_pokemon_info(self, name: str):
        resp = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name}")
        return resp.json()

    def get_pokemon_type(self, name: str) -> str:
        resp_json = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name}").json()
        types = []
        for type_data in resp_json["types"]:
            types.append(type_data["type"]["name"])

        return str(types)
    
    def __str__(self):
        return (f"Name: {self.name}\n"
                f"ID: {self.ident}\n"
                f"Details: {self.details}\n"
                f"Condition: {self.condition}\n"
                f"Active: {self.active}\n"
                f"Stats: {self.stats}\n"
                f"Moves: {', '.join(self.moves)}\n"
                f"Item: {self.item}\n"
                f"Ability: {self.ability}")

