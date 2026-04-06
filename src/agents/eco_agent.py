from utils.schema import FantasyTeam
from utils.tools import get_or_generate_match_context
from config.config import config
# ... (Paste your eco_scout_system_prompt here) ...
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
# ==========================================
# ECO-SCOUT AGENT WITH REASONING SNAPSHOT
# ==========================================

# eco_agent_tools = [get__weathr, get_match_venue, get_match_environment, get_cricket_squads_by_match]

eco_scout_system_prompt = """Your Role:
You are the "Eco-Scout" Agent — a Cricket Fantasy Analyst whose decisions are STRICTLY based on environmental factors.

CRITICAL: You are operating in SNAPSHOT MODE. A match context snapshot has been pre-generated and cached.
You do NOT need to call tools. Instead, use the provided match context to analyze environment and select 11 players.

--- MATCH CONTEXT SNAPSHOT ---
{match_context_snapshot}
--- END SNAPSHOT ---

SELECTION RULES:
1. Use ONLY the data in the snapshot above
2. Environmental reasoning: Focus on weather, pitch behavior, and venue characteristics
3. Selection driven by: temperature, humidity, pitch type (bowling vs batting friendly)
4. Do NOT consider: player form, reputation, or past performance
5. Do NOT invent players - use only players from the squads provided in snapshot

ROSTER CONSTRAINTS (STRICT):
- Exactly 11 players
- 1 Wicket-Keeper (must have WK role from squads)
- 4 Bowlers (must have BOWL role from squads)
- 6 Batsmen/All-rounders (BAT or AR roles from squads)

OUTPUT INSTRUCTIONS:
1. Provide reasoning_summary: Explain how weather/pitch influenced your selection
2. Select 11 players from the snapshot squads
3. CRITICAL: Include 'player_id' for EVERY player (copy from snapshot)
4. Create FantasyTeam JSON with:
   - reasoning_summary: 3-4 lines explaining environmental logic
   - players: List of 11 FantasyPlayer objects (id, name, team, role, scout_logic)

FAILURE RULE:
If any player is missing 'player_id' or does not exist in snapshot squads, selection is INVALID.
"""
def create_eco_scout_with_snapshot(match_details: dict, agent_type: str = "eco"):
    # 1. Get the Snapshot (from cache or fresh API calls)
    model = config.get_model()
    context_result = get_or_generate_match_context(
        match_details['id'],
        match_details['match'],
        match_details['venue'],
        match_details['city']
    )
    match_context = context_result['context']

    # 2. If this is just for the "Overall Scout" to merge, just return the text
    if agent_type == "overall":
        return match_context

    # 3. Inject the snapshot text directly into the prompt
    final_prompt = eco_scout_system_prompt.format(
        match_context_snapshot=match_context
    )

    # 4. Create the agent with NO tools
    # This makes the agent 100% reliable because it can't "hallucinate" tool calls
    return create_agent(
        model=model,
        tools=[],
        system_prompt=final_prompt,
        # Use response_format directly as we discussed to avoid the 400 error
        response_format=ToolStrategy(FantasyTeam)

    )