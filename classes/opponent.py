from classes.pokemon import Pokemon
from typing import List, Optional, Dict

class Trainer:
    def __init__(self, name: str, id: str, team: Optional[Dict[str, Pokemon]] = None):
        self.name = name
        self.id = id
        self.team = team if team is not None else {}

    def get_active_pokemon(self) -> Optional[Pokemon]:
        for pokemon in self.team.values():
            if pokemon.active:
                return pokemon
        return None

    def get_team(self) -> Dict[str, Pokemon]:
      return self.team

    def insert_pokemon(self, pokemon: Pokemon):
        self.team[pokemon.name] = pokemon
    
    def update_pokemon(self, key: str, updated_pokemon: Pokemon):
        if key in self.team:
            self.team[key] = updated_pokemon
        else:
            print(f"Pokémon with key {key} not found in team.") 
 
