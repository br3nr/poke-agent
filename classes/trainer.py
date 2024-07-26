from typing import List, Dict
from classes.pokemon import Pokemon


class Trainer:

    def __init__(self, name: str, id: str, team: List[Pokemon]):
        self.name = name
        self.id = id
        self.team = team

    def get_active_pokemon(self) -> Pokemon:
        for pokemon in self.team:
            if pokemon.active == True:
                return pokemon
        return None

    def get_team(self) -> List[Pokemon]:
        return self.team
