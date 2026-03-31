from typing import List, Dict
from classes.opponent import Opponent
from classes.trainer import Trainer

class BattleData():

    def __init__(self):
        self.trainer: Trainer = None
        self.battle_log: List[str] = []
        self.move_queue: List[str] = []
        self.opponent = Opponent(pid="p2a")
        self.battle_id = None