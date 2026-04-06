# agents/router.py
from agents.form_agent import create_form_scout_with_snapshot
from agents.eco_agent import create_eco_scout_with_snapshot
from agents.overall_agent import run_overall_merge_scout  # Import the agent object
from utils.tools import get_started_matches_report
from agents.scout_tools import call_form_scout
from agents.scout_tools import call_eco_scout
from config.config import config
import time
_CACHED_LIVE_MATCHES = None
_LAST_MATCH_SYNC = 0
def fantasy_team_router(user_query: str):
    """
    The MAIN CALL for the entire system.
    Decides whether to show matches, call a single scout, or merge.

    """
    global _CACHED_LIVE_MATCHES, _LAST_MATCH_SYNC
    try:
        query_lower = user_query.lower()
        current_time = time.time()

        # --- 1. THE ROUTER SHIELD ---
        # Check if we already have the matches in memory (less than 10 mins old)
        if _CACHED_LIVE_MATCHES and (current_time - _LAST_MATCH_SYNC < 600):
            print("🛡️ [ROUTER MEMORY] Using matches from previous player (Skipping Sheet Call)")
            live_matches = _CACHED_LIVE_MATCHES
        else:
            print("🌐 [ROUTER SYNC] First player or Cache expired. Calling Sheet...")
            live_matches = get_started_matches_report.invoke({})

            # Save to memory for the next 59 players
            _CACHED_LIVE_MATCHES = live_matches
            _LAST_MATCH_SYNC = current_time

        # --- 2. Handle the Result (Same as before) ---
        if any(word in query_lower for word in ["matches", "today", "available"]):
            return live_matches

        if isinstance(live_matches, str):
            return live_matches

        if not live_matches:
            return "⚠️ No active matches found."

        target_match = live_matches[0]


        # --- 3. Route to specific Agent ---
        if "form" in query_lower:
            # Note: You'll need to call your form agent executor here

            return call_form_scout.invoke({"match_details": target_match})

        elif "eco" in query_lower:
            print('inside eco')

            return call_eco_scout.invoke({"match_details": target_match})

        elif any(word in query_lower for word in ["best", "overall", "merge"]):
            print(f"🚀 MERGE CASE: Fetching raw snapshots...")

            # Call your specialized snapshot functions
            form_context = create_form_scout_with_snapshot(target_match, agent_type="overall")
            eco_context = create_eco_scout_with_snapshot(target_match, agent_type="overall")

            merge_input = f"PLAYER FORM:\n{form_context}\n\nECO DATA:\n{eco_context}"

            overall=run_overall_merge_scout(form_context,eco_context)

            # Call the Director (Merge Agent)
            final_result = overall.invoke({"input": merge_input})

            # Return the JSON string
            if hasattr(final_result, 'model_dump_json'):
                return final_result.model_dump_json(indent=2)
            return str(final_result)

        return "Please ask for 'Form', 'Eco', or 'Overall' team."
    finally:
        # 🎯 THIS RUNS NO MATTER WHICH 'RETURN' WAS TRIGGERED ABOVE
        # It ensures the 'Fridge' is updated before the request ends.
        print("completed for a request")

