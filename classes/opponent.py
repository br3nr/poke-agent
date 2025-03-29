from classes.pokemon import Pokemon
from typing import List, Optional, Dict

class Opponent:

    def __init__(self, pid: str):

        self.pid = pid
        self.team: List[Pokemon] = []
        self.active_pokemon = ""

    def update_active_pokemon(self, name: str):
        self.active_pokemon = name

