import os
import time
from dotenv import load_dotenv
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from rich import print
from google.api_core.exceptions import ResourceExhausted
import google.generativeai as genai

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END

from utils.config import safety_filters
from classes.battle_data import BattleData
from classes.agent_toolkit import AgentToolkit
from classes.sharedstate import SharedState
from typing_extensions import TypedDict
from typing import List
from textwrap import dedent

class BattleLog(TypedDict):
    log: str
    summary: str

class HistoryAgent:
    def __init__(self, battle_data: BattleData):
        self.toolkit = AgentToolkit(battle_data)
        self.battle_data = BattleData()
        self.llm = genai.GenerativeModel(
            model_name="gemini-2.0-flash-lite",
            generation_config={"temperature": 0},
            safety_settings=safety_filters,
        )

        self.graph = StateGraph(BattleLog)  # Create a new graph

        self.graph.add_node("get_history", self.get_history)

        # Define entry point and edges
        self.graph.set_entry_point("get_history")

        # Compile the graph
        self.executor = self.graph.compile()

    def get_history(self, state: BattleLog):

        #user_input = state["input"]
        #response = self.llm.invoke(user_input)
        chat = self.llm.start_chat()

        msg = dedent(""" 
            You are an AI designed to process Pokémon battle logs into a structured, concise, and unambiguous format. 
            Your goal is to extract key battle events while maintaining a clear and readable log.  
            P1 in this scenario is player, and P2 is the opponent. Because of this we have less info about the opponent.

            ### **Instructions:**
                - Follow the provided **output format** exactly.  
                - **Do not infer** any unlogged actions. Only use explicitly stated information.  
                - Use **consistent phrasing** for damage, healing, item activation, and switches.  
                - Track **HP changes** clearly (`Before → After`).  
                - Log **item and ability activations** in a standard format.  
                - Include a **brief summary** highlighting key effects.  
            
            Your output will be critical, as it will be used by the team leader. They will make a decision based on this log and previos ones.
            Therefor it is imperative to include things like how effective the move was (super effective, not very effective, etc), along with status effects.
            However, you must base your report based on what you see in the log, do not make any of your own assumptions.

            ### **Example Battle Log**
            |move|p1a: Carbink|Power Gem|p2a: Vikavolt
            |-supereffective|p2a: Vikavolt
            |-damage|p2a: Vikavolt|52/100
            |move|p2a: Vikavolt|Toxic|p1a: Carbink
            |-status|p1a: Carbink|tox
            |
            |-heal|p2a: Vikavolt|58/100| item: Leftovers
            |-damage|p1a: Carbink|180/236 tox| psn

            In this battle log, we can see that p1a has a Carbink has used Power Gem vs p2a's Vikavolt. 
            The move was super effective. The damage left Vikavolt with 52% of its health out of 100%.
            The enemy p2a moves next, and uses toxic against Carbink, which we can see was effective due to the staus effect.
            Vikavolt then uses Leftovers to regain health, followed by Carbink taking toxic damage reducing it to 180/236 HP.
            We can see the exact HP for our Carbink, but only the % for the enemy.

            ### **Output Format:**  
                For the current battle step, generate the following structured log:

                **Pokémon:** `p1: {Pokémon Name} ({HP Before} → {HP After})`, `p2: {Pokémon Name} ({HP % Before} → {HP % After})`  
                **Actions:**  
                - `{Attacker} used {Move} on {Target} ({Effect: [Damage/Boosts/Resistances]})`  
                - `{Pokémon} healed {Amount} (Item: {Item}, {HP Before} → {HP After})`  
                - `{Pokémon} switched in/out (HP: {Current HP})`  
                - `{Ability} activated ({Effect})`  
                **Summary:** `{Key event description}`  

            You are about to receive a battle log for the current step / turn in the game. 
            Battle Log:\n 
        """) + state["log"]

        response = None
        while response is None:
            try:
                response = chat.send_message(msg).text
            except ResourceExhausted:
                print("[bold purple]Sleeping...[/bold purple]")
                time.sleep(15)

        state["summary"] = response
        return state 


    def execute_agent(self, log: str):
        return self.executor.invoke({"log":log})

