import time
from textwrap import dedent
from rich import print
from google.api_core.exceptions import ResourceExhausted
import google.generativeai as genai
from langgraph.graph import StateGraph

from utils.config import safety_filters
from classes.sharedstate import SharedState


class DecisionAgent:
    def __init__(self):
        self.llm = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            safety_settings=safety_filters,
        )

        self.graph = StateGraph(SharedState)
        self.graph.add_node("get_decision", self.get_decision)
        self.graph.set_entry_point("get_decision")
        self.executor = self.graph.compile()

    def get_decision(self, state: SharedState):
        chat = self.llm.start_chat()

        msg = dedent(f"""
        You are in a team of professional pokemon players. Together you are united in a competitive battle in Pokemon Showdown.
        Your role in the team is Team Captain. You are the one who will make decisions based on the state of the game.
        The Team Researcher has provided you with the following details about the state of the game:

            Analysis: '{state["analysis"]}'

        Given the above analysis, you must now make the call on what the best decision is.

        You have two options:
            1) Attack with one of the current moves (specify the exact move name)
            2) Switch pokemon (specify the exact pokemon name to switch to)

        You should rely on the information provided in the analysis. It is imperative that you only use common knowledge where relevant.

        When you decide what to do, you should consider many things, including:
            - The state of your current pokemon, and others in your team. 
            - What the opponent might do next. I.e., will they likely swap to another pokemon, will they pre-empt anything? 
            - Is your current pokemon or any of your moves effective against your pokemon? 
            - Do you suspect your opponent might switch, or have they done this before? Does this impact what move you use now?
            - Are there any weather effects, terrains, etc on the field?
            - Should you think ahead, or stay in the present moment?
            - Are there any stat boosting moves, status effect moves (like poison) or other moves that are worth using now rather that going for damage?
            - Are there any abilities or items that you or the opponent have to consider?

        Once you have decided, concisely explain your logic. Give it in a bullet list. It must not be verbose.
        As in, maximum 10 bullet points.
        Once you have explained, instruct the Team Battler on what they should do.
        End your response stating either:
        USE MOVE: <move_name>
        or
        SWITCH TO: <pokemon_name>
        """)

        response = None
        while response is None:
            try:
                response = chat.send_message(msg).text
            except ResourceExhausted:
                print("[bold purple]Sleeping...[/bold purple]")
                time.sleep(15)

        print(f"[bold magenta]Decision Agent\n{response}[/bold magenta]")

        state["decision"] = response
        return state

    def execute_agent(self, state: SharedState):
        return self.executor.invoke(state)
