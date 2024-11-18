from typing import List, Dict
from classes.opponent import Opponent


class SingletonMetaclass(type):
    """Metaclass Singleton Pattern"""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class BattleData(metaclass=SingletonMetaclass):
    """Until I can find out how to share data to a tool, without having it all in one class, I will use a singleton.
    Will I do a project without using a singleton? I do not know.
    """

    def __init__(self):
        self.trainer = None
        self.battle_log: List[str] = []
        self.move_queue: List[str] = []
        self.opponent = Opponent(pid="p2a")
