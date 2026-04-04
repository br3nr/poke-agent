"""
AnalysisAgent - The Team Researcher

Gathers comprehensive battle state information using available tools.
Produces a structured analysis report for the DecisionAgent.
"""

import time
from textwrap import dedent
from rich import print
from google.api_core.exceptions import ResourceExhausted
import google.generativeai as genai
from langgraph.graph import StateGraph

from poke_env.battle import Battle

from utils.config import safety_filters
from classes.agent_toolkit import AgentToolkit
from classes.sharedstate import SharedState


class AnalysisAgent:
    def __init__(self, battle: Battle, toolkit: AgentToolkit):
        self.battle = battle
        self.toolkit = toolkit

        self.llm = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            tools=[
                self.toolkit.get_pokemon_details,
                self.toolkit.get_current_moves,
                self.toolkit.get_opponent_pokemon_details,
                self.toolkit.get_team_details,
                self.toolkit.check_type_advantages,
                self.toolkit.get_available_switches,
            ],
            generation_config={"temperature": 0},
            safety_settings=safety_filters,
        )

        self.graph = StateGraph(SharedState)
        self.graph.add_node("get_analysis", self.get_analysis)
        self.graph.set_entry_point("get_analysis")
        self.executor = self.graph.compile()

    def get_analysis(self, state: SharedState):
        chat = self.llm.start_chat(enable_automatic_function_calling=True)

        # Get current pokemon names from poke-env battle object
        active_pokemon = self.battle.active_pokemon
        opponent_pokemon = self.battle.opponent_active_pokemon

        active_name = active_pokemon.species if active_pokemon else "Unknown"
        opponent_name = opponent_pokemon.species if opponent_pokemon else "Unknown"

        msg = dedent(f""" 
            **Team Analysis Report**

            You are the researcher in a professional Pokemon battle team. Your job is to gather and report all available facts about the battle.  

            Your current pokemon is {active_name}
            You are currently facing off against {opponent_name}.

            ### **Your Task:**
            1. Use the available tools to collect detailed information.
            2. List **all** retrieved data in a structured format.
            3. Do **not** summarize, interpret, or omit any details.

            ---

            ### **What You Must Gather:**
            - **Your Pokemon Details**: Call `get_pokemon_details` on your active Pokemon ({active_name}).
            - **Your Pokemon's Available Moves**: Call `get_current_moves`.
            - **Opponent's Pokemon Details**: Call `get_opponent_pokemon_details` on the opposing Pokemon ({opponent_name}).
            - **Type Matchups & Advantages**: Call `check_type_advantages` for the opponent's Pokemon.
            - **Your Team Details**: Call `get_team_details` to list all available team members.
            - **Available Switches**: Call `get_available_switches` to see which Pokemon you can switch to.

            **You must call each function and include all retrieved information in your response.**  

            Begin your report now.""")

        response_text = None
        while response_text is None:
            try:
                response = chat.send_message(msg)
                # Handle case where model returns function calls but no text
                try:
                    response_text = response.text
                except ValueError:
                    # No text in response, ask for summary
                    response = chat.send_message(
                        "Now provide your complete analysis report as text."
                    )
                    response_text = response.text
            except ResourceExhausted as e:
                print(f"[bold purple]Rate limited: {e}. Sleeping 15s...[/bold purple]")
                time.sleep(15)
            except Exception as e:
                print(f"[bold red]Analysis error: {type(e).__name__}: {e}[/bold red]")
                raise

        print(
            f"[bold bright_yellow]Analysis Agent\n{response_text}[/bold bright_yellow]"
        )

        state["analysis"] = response_text
        return state

    def execute_agent(self, state: SharedState):
        return self.executor.invoke(state)
