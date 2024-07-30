from classes.pokemon import Pokemon
from typing import List, Optional, Dict

class Trainer:
    def __init__(self, name: str, id: str, team: Optional[List[Pokemon]] = None, active_moves: Optional[List[Dict]] = None):
        self.name = name
        self.id = id
        self.team = team if team is not None else []
        self.active_moves = active_moves
    
    def get_active_pokemon(self) -> Optional[Pokemon]:
        for pokemon in self.team:
            print(pokemon.name)
            if pokemon.active:
                return pokemon
        return None

    def get_next_available(self) -> int | None:
        for i, pokemon in enumerate(self.team):
            if(pokemon.condition != "0 fnt" and pokemon.active != True):
                return i+1
        return None

    def get_team(self) -> List[Pokemon]:
        return self.team

    def insert_pokemon(self, pokemon: Pokemon):
        self.team.append(pokemon)
    
    def update_pokemon(self, name: str, updated_pokemon: Pokemon):
        for i, pokemon in enumerate(self.team):
            if pokemon.name == name:
                self.team[i] = updated_pokemon
                return
        print(f"Pokémon with name {name} not found in team.") 

