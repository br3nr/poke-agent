import os
import time
from dotenv import load_dotenv
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from rich import print
from google.api_core.exceptions import ResourceExhausted
import google.generativeai as genai
from textwrap import dedent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END

from utils.config import safety_filters
from classes.battle_data import BattleData
from classes.agent_toolkit import AgentToolkit
from classes.sharedstate import SharedState

class AnalysisAgent:
    def __init__(self, battle_data: BattleData):
        self.toolkit = AgentToolkit(battle_data)
        self.battle_data = battle_data
        self.llm = genai.GenerativeModel(
            model_name="gemini-2.5-flash-preview-05-20",
            tools=[
                self.toolkit.get_pokemon_details,
                self.toolkit.get_current_moves,
                self.toolkit.get_opponent_pokemon_details,
                self.toolkit.get_team_details,
                self.toolkit.check_type_advantages,
            ],
            generation_config={"temperature": 0},
            safety_settings=safety_filters,
        )

        self.graph = StateGraph(SharedState)  # Create a new graph

        self.graph.add_node("get_analysis", self.get_analysis)

        # Define entry point and edges
        self.graph.set_entry_point("get_analysis")

        # Compile the graph
        self.executor = self.graph.compile()

    def get_analysis(self, state: SharedState):

        chat = self.llm.start_chat(enable_automatic_function_calling=True)

        msg = dedent(f""" 
            **Team Analysis Report**

            You are the researcher in a professional Pokémon battle team. Your job is to gather and report all available facts about the battle.  

            Your current pokemon is {self.battle_data.trainer.get_active_pokemon().name}
            You are currently facing off against a {self.battle_data.opponent.active_pokemon}.

            ### **Your Task:**
            1. Use the available tools to collect detailed information.
            2. List **all** retrieved data in a structured format.
            3. Do **not** summarize, interpret, or omit any details.

            ---

            ### **What You Must Gather:**
            - **Your Pokémon Details**: Call `get_pokemon_details` on the active Pokémon.
            - **Your Pokémon's Available Moves**: Call `get_current_moves`.
            - **Opponent's Pokémon Details**: Call `get_opponent_pokemon_details` on the opposing Pokémon.
            - **Type Matchups & Advantages**: Call `check_type_advantages` for the active Pokémon.
            - **Your Team Details**: Call `get_team_details` to list all available team members.

            **You must call each function and include all retrieved information in your response.**  

            Begin your report now."""
        )

        response = None
        while response is None:
            try:
                response = chat.send_message(msg).text
            except ResourceExhausted:
                print("[bold purple]Sleeping...[/bold purple]")
                time.sleep(15)

        print(
            f"[bold bright_yellow]Analysis Agent\n{response}[/bold bright_yellow]"
        )
         
        state["analysis"] = response
        return state 


    def execute_agent(self, state: SharedState):
        return self.executor.invoke(state)

