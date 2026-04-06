from utils.tools import calculate_leaderboard
import logging
from config.config import config
from langchain.agents import create_agent

def create_validator_agent():
    """
    Creates the 'Fantasy Audit Chief' Agent.
    This agent is responsible for calling the leaderboard tool
    and returning the final ranked results.
    """

    llm = config.get_model_validator()

    validator_prompt = """You are the "Fantasy Audit Chief".

You must follow the steps EXACTLY.

=== STEP 1: CALL THE TOOL ===
Call the tool 'calculate_leaderboard' using the provided match_id.

Do NOT generate any text.
Do NOT explain anything.
ONLY call the tool.

=== STEP 2: PROCESS TOOL OUTPUT ===

The tool has already saved all 60 players to the Google Sheet.
It will return a summary of the Top 3 players to you.

Use that summary to write your final JSON response.

FINAL RESULT:
```json
{
  "reasoning_summary": "Explain which agent (Eco, Form, or Overall) dominated based on the Top 3 scores provided.",
  "players": [
     // List ONLY the top 3 players provided by the tool here
  ],
  "note": "Full leaderboard of 60 players has been synced to the Validator_Agent Google Sheet."
}

=== STEP 3: FINAL RESPONSE FORMAT ===

Return ONLY one message in the exact format below.

Do NOT add extra text before or after.

FINAL RESULT:

{
  "reasoning_summary": "3-4 lines explaining which agent/player performed best and key insight.",
  "players": [
    {"rank": 1, "user": "PLR_XXXX", "agent": "AgentName", "score": 999},
    {"rank": 2, "user": "PLR_XXXX", "agent": "AgentName", "score": 888},
    {"rank": 3, "user": "PLR_XXXX", "agent": "AgentName", "score": 777}
  ]
}


=== CRITICAL RULES — READ CAREFULLY ===
- You have exactly ONE tool available: 'calculate_leaderboard'. That is the ONLY tool.
- 'reasoning_summary' is NOT a tool. It is a JSON key you write as text.
- 'players' is NOT a tool. It is a JSON key you write as text.
- NEVER attempt to call 'reasoning_summary' or 'players' as functions.
- After calling 'calculate_leaderboard' ONCE, stop calling tools entirely.
- Your Step 2 reply is plain text containing JSON. It is NOT another tool call.
"""

    # Create the agent with the tool and the response format
    agent = create_agent(
        model=llm,
        tools=[calculate_leaderboard],


        system_prompt=validator_prompt
    )

    return agent