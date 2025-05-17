from typing_extensions import TypedDict
from typing import List

class SharedState(TypedDict):
    analysis: str
    decision: str
    history: List[str]
