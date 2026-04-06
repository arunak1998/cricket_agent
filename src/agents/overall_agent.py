from utils.schema import FantasyTeam
# Assuming you have a factory or direct create_agent call
from langchain.agents import create_agent
from config.config import config
# 1. THE SYSTEM PROMPT (Optimized for JSON Output)
MERGE_PROMPT = """You are the "Ultimate Fantasy Director".
Your task is to build a winning 'Playing 11' by merging two specialized data streams:
1. PLAYER FORM DATA (Recent performances, strike rates, wickets).
2. ECO/VENUE DATA (Pitch behavior, weather, venue dimensions).

--- INPUT DATA STREAMS ---
{combined_snapshots}
--- END DATA STREAMS ---

CRITICAL RULES:
1. DATA SOURCE: Only use players provided in the input text above. Never hallucinate.
2. BALANCE: Select exactly 11 players. (1 WK, 4 BOWL, 6 BAT/AR).
3. LOGIC: Compare 'Form' (who is playing well) with 'Eco' (whose style fits this pitch).
4. IDENTIFICATION: You MUST preserve the exact 'player_id' for every player.

OUTPUT INSTRUCTIONS:
Return a FantasyTeam JSON object with:
- reasoning_summary: 3-4 lines explaining how Form was balanced against Venue conditions.
- players: List of 11 FantasyPlayer objects (player_id, name, team, role, scout_logic).
"""

# 2. THE MERGE FUNCTION
def run_overall_merge_scout(form_snapshot: str, eco_snapshot: str):
    """
    Takes the text snapshots from Form-Scout and Eco-Scout
    and produces the final merged 11-player team.
    """

    # Combine the two snapshots into one big block of text
    combined_data = f"""
    === [STREAM 1: PLAYER FORM] ===
    {form_snapshot}

    === [STREAM 2: ECO & VENUE] ===
    {eco_snapshot}
    """

    # Inject the data into the prompt
    final_system_prompt = MERGE_PROMPT.format(combined_snapshots=combined_data)
    model = config.get_model()

    # Create the agent
    # We use response_format=FantasyTeam (Native JSON) because there are NO tools.
    # This avoids the 400 error we discussed!
    agent = create_agent(
        model=model,
        tools=[],
        system_prompt=final_system_prompt,
        response_format=FantasyTeam
    )

    # Execute the agent
    # Since it's a zero-tool agent with a strict schema, it returns the JSON immediately.
    print("🔄 Ultimate Director is merging Form and Eco data...")
    return agent