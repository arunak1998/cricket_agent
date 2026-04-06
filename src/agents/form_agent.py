from utils.schema import FantasyTeam
from utils.tools import get_or_generate_match_context_for_form
import logging
from config.config import config
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from typing import Union
# ==========================================
# FORM-SCOUT AGENT WITH REASONING SNAPSHOT
# ==========================================
logger = logging.getLogger(__name__)
form_scout_system_prompt = """Your Role:
You are the "Form-Scout" Agent — a Cricket Fantasy Analyst whose decisions are STRICTLY driven by player form.

CRITICAL: You are operating in SNAPSHOT MODE. A match context snapshot has been pre-generated and cached.
You do NOT need to call tools. Instead, use the provided match context to analyze form and select 11 players.

--- MATCH CONTEXT SNAPSHOT ---
{match_context_snapshot}
--- END SNAPSHOT ---

FORM-BASED SELECTION RULES:
1. Use ONLY the data in the snapshot above (venue, squads, and player stats)
2. Form analysis: Focus on strike rates (SR > 140), wicket-taking records, recent momentum
3. Selection driven by: Player recent form (T20 stats), venue alignment, value picks (all-rounders)
4. Do NOT consider: Past seasons, intuition, or non-provided data
5. Do NOT invent players - use only players from the squads in snapshot

FORM SCORING LOGIC:
- High Strike Rate (SR > 140): Strong batting form indicator
- Wicket Takers (3+ wickets in recent): Top bowlers
- All-rounders: Both batting AND bowling stats in form
- Venue Alignment: Match high-scorers with power venues, bowlers with defensive venues

ROSTER CONSTRAINTS (STRICT):
- Exactly 11 players
- 1 Wicket-Keeper (must have WK role from squads, highest recent T20 runs)
- 4 Bowlers (must have BOWL role from squads, top 4 wicket-takers in recent form)
- 6 Batsmen/All-rounders (BAT or AR roles from squads, prioritize SR > 140)

OUTPUT INSTRUCTIONS:
1. Provide reasoning_summary: Explain player form analysis and venue alignment
2. Select 11 players from the snapshot squads
3. CRITICAL: Include 'player_id' for EVERY player (copy from snapshot)
4. Create FantasyTeam JSON with:
   - reasoning_summary: 3-4 lines explaining form-based selection logic
   - players: List of 11 FantasyPlayer objects (id, name, team, role, scout_logic)

FAILURE RULE:
If any player is missing 'player_id' or does not exist in snapshot squads, selection is INVALID.
"""

def create_form_scout_with_snapshot(match_details: Union[str, dict], agent_type: str = "form"):
    """
    Factory function to create Form-Scout agent or return context for Merging.
    """
    logger.info(f"🔍 Form-Scout initializing for: {match_details['id']} | Mode: {agent_type}")

    # 1. Get or generate match context snapshot
    context_result = get_or_generate_match_context_for_form(match_details['id'], match_details['match'])
    match_context = context_result['context']

    # --- NEW LOGIC FOR OVERALL SCOUT ---
    # If we are just preparing data for the "Overall" merge, stop here and return the string context.
    if agent_type == "overall":
        logger.info(f"📤 Returning match_context only for Overall-Scout merge.")
        return match_context

    # --- ORIGINAL LOGIC FOR FORM SCOUT ---
    is_cached = context_result.get('is_cached', False)
    status = "📦 [CACHED]" if is_cached else "📸 [FRESH]"
    logger.info(f"{status} Form-Scout context ready ({len(match_context)} chars)")

    # Inject snapshot into system prompt
    final_system_prompt = form_scout_system_prompt.format(
        match_context_snapshot=match_context
    )
    model = config.get_model()
    # Create agent
    agent = create_agent(
        model=model,
        tools=[],
        system_prompt=final_system_prompt,
        response_format=ToolStrategy(FantasyTeam)
    )

    return agent
