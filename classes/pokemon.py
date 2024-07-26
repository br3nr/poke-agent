from typing import List, Dict


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
