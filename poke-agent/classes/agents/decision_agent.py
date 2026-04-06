import time
from textwrap import dedent

from google import genai
from google.genai import types
from google.genai.errors import ClientError

from utils.config import safety_filters
from utils.logging import log_decision_reasoning, log_rate_limit, log_token_usage
from classes.sharedstate import SharedState

MODEL = "gemini-3-flash-preview"


class DecisionAgent:
    def __init__(self):
        self.client = genai.Client()

    def get_decision(self, state: SharedState):
        msg = dedent(f"""
        You are in a team of professional pokemon players. Together you are united in a competitive battle in Pokemon Showdown.
        Your role in the team is Team Captain. You are the one who will make decisions based on the state of the game.
        The Team Researcher has provided you with the following details about the state of the game:

            Analysis: '{state["analysis"]}'

        Given the above analysis, you must now make the call on what the best decision is.

        You have three options:
            1) Attack with one of the current moves (specify the exact move name)
            2) Switch pokemon (specify the exact pokemon name to switch to)
            3) Terastallize and attack with one of the current moves (only if tera is available this turn)

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
            - Would Terastallizing give a significant type advantage, STAB boost, or defensive benefit right now? Don't waste it frivolously.

        Once you have decided, concisely explain your logic. Give it in a bullet list. It must not be verbose.
        As in, maximum 10 bullet points.

        Once you have decided, end your response stating one of:
        USE MOVE: <move_name>
        or
        SWITCH TO: <pokemon_name>
        or
        TERASTALLIZE AND USE MOVE: <move_name>
        """)

        result = None
        while result is None:
            try:
                result = self.client.models.generate_content(
                    model=MODEL,
                    contents=msg,
                    config=types.GenerateContentConfig(
                        safety_settings=safety_filters,
                        thinking_config=types.ThinkingConfig(
                            thinking_level="LOW",
                        ),
                    ),
                )
            except ClientError as e:
                if e.code == 429:
                    log_rate_limit()
                    time.sleep(15)
                else:
                    raise

        # track token usage
        meta = result.usage_metadata
        if meta:
            log_token_usage(
                prompt_tokens=meta.prompt_token_count,
                completion_tokens=meta.candidates_token_count,
                thinking_tokens=meta.thoughts_token_count,
            )

        response = result.text
        log_decision_reasoning(response)

        state["decision"] = response
        return state

    def execute_agent(self, state: SharedState):
        return self.get_decision(state)
