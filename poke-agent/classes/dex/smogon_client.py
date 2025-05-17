import requests
import random
from typing import List, Optional, Dict

class SmogonClient:
    BASE_URL = "https://www.smogon.com/dex/_rpc/"

    @staticmethod
    def get_basics(gen: str) -> dict:
        url = f"{SmogonClient.BASE_URL}dump-basics"
        payload = {"gen": gen}
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_pokemon(gen: str, pokemon: str) -> dict:
        url = f"{SmogonClient.BASE_URL}dump-pokemon"
        payload = {"gen": gen, "alias": pokemon, "language": "en"}
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_format(gen: str, format: str) -> dict:
        url = f"{SmogonClient.BASE_URL}dump-format"
        payload = {"gen": gen, "alias": format, "language": "en"}
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def get_random_pokemon(self, gen: str) -> dict:
        basics = self.get_basics(gen)
        pokemon_list = [p for p in basics['pokemon'] if p.get('is_non_standard') == "Standard"]
        if not pokemon_list:
            raise ValueError("No standard Pokémon found for this generation.")
        return random.choice(pokemon_list)

    def get_moveset(self, gen: str, pokemon_name: str, format: Optional[str] = None) -> Optional[Dict[str, List[str]]]:
        pokemon_data = self.get_pokemon(gen, pokemon_name.lower().replace(' ', '-'))
        strategies = pokemon_data.get('strategies', [])

        if format:
            strategies = [s for s in strategies if s['format'] == format]

        if not strategies:
            return None

        strategy = random.choice(strategies)
        if not strategy['move_sets']:
            return None

        move_set = random.choice(strategy['move_sets'])
        moves = [move['move'] for move in move_set['moves']]
        return {"format": strategy['format'], "moves": moves}

# Example usage:
client = SmogonClient()

# Fetch basic Pokémon data for a generation
gen = "sv"  # Generation value (e.g., sv, ss, sm, etc.)
basics = client.get_basics(gen)
print(basics)

# Fetch specific Pokémon data
pokemon_name = "Pikachu"
pokemon_data = client.get_pokemon(gen, pokemon_name)
print(pokemon_data)

# Fetch specific format data
format_name = "ou"
format_data = client.get_format(gen, format_name)
print(format_data)

# Get a random Pokémon and its moveset
random_pokemon = client.get_random_pokemon(gen)
print(random_pokemon)

moveset = client.get_moveset(gen, random_pokemon['name'], format_name)
print(moveset)

# Fetch moveset for a specific Pokémon (e.g., "Earthquake" for a specific Pokémon)
specific_pokemon_name = "Garchomp"
specific_moveset = client.get_moveset(gen, specific_pokemon_name, format_name)
print(specific_moveset)
