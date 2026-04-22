# poke-agent

Poke-agent is an AI-powered Pokemon Showdown battle agent that uses Google Gemini to play competitive Pokemon battles autonomously.

This is currently a work in progress. Initially, this was based around a multi-agent system for managing each step in a battle, however due to speed constraints and token usage, a sequential execution is currently being used.

Version 2 will reintroduce more agentic behaviour into the system in order to better reason about each move. 

### High Level Overview

Each turn, three steps run sequentially:

1. **Analysis** - Gathers structured battle state: your team, opponent info, type matchups, move effectiveness, field conditions, and turn history.
2. **Decision** - Sends the analysis to Gemini 2.5 Flash and returns a decision with reasoning.
3. **Battle** - Parses the LLM output into a game command. 

## Setup

**Requirements:** Python 3.12+, [uv](https://github.com/astral-sh/uv)

```bash
git clone https://github.com/br3nr/poke-agent.git
cd poke-agent/poke-agent
uv sync
```

Create a `.env` file:

```
GOOGLE_API_KEY=your_api_key
SHOWDOWN_USERNAME=username
SHOWDOWN_PASSWORD=password
```

## Usage

```bash
# Test locally against a random bot
python showdown.py --test

# Run multiple battles
python showdown.py --test -n 5

# Go online and accept challenges
python showdown.py --online

# Challenge a specific player
python showdown.py --challenge <username>

# Play ranked ladder
python showdown.py --ladder -n 5
```
