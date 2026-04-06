# main.py
from agents.router import fantasy_team_router
from agents.validator_agent import create_validator_agent
import gspread
import json
from google.auth import default
from config.config import config
from oauth2client.service_account import ServiceAccountCredentials
import os
# 1. Setup Connection
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

def get_gspread_client():
    """
    Dynamically connects to Google Sheets based on the environment.
    """
    # Path to your local key (Adjust this for your local PC)
    local_key = "/mnt/c/workspaces/agent_project/src/credentials.json"

    if os.path.exists(local_key):
        # --- LOCAL MODE ---
        print("💻 [LOCAL] Found credentials.json. Connecting via Service Account Key...")
        creds = ServiceAccountCredentials.from_json_keyfile_name(local_key, scope)
        return gspread.authorize(creds)
    else:
        # --- CLOUD MODE ---
        print("☁️ [CLOUD] No local key found. Connecting via Cloud Run Service Identity...")
        try:
            # This 'default()' function is built into the google-auth library
            # It automatically finds the Cloud Run Service Account
            creds, project = default(scopes=scope)
            return gspread.authorize(creds)
        except Exception as e:
            raise Exception(f"❌ Failed to connect to Google Sheets in any environment: {e}")

# 2. Initialize the client dynamically
client = get_gspread_client()

# 3. Open your Sheet
spreadsheet_name = "Cricket_Project_DB."
spreadsheet = client.open(spreadsheet_name)
import time

def update_agent_responses():
    # ── 1. Load Player_agentsheet ──────────────────────────────────────────
    player_sheet = spreadsheet.worksheet("Player_agent")
    all_values = player_sheet.get_all_values()
    headers = all_values[0]
    data_rows = all_values[1:]

    print("Headers found:", headers)
    print(f"Total players found: {len(data_rows)}")

    # ── 2. Prepare response sheet ──────────────────────────────────────────
    response_sheet = spreadsheet.worksheet("Agent_Response")
    response_sheet.batch_clear(["A2:D1000"])

    rows_to_write = []

    # ── 3. Loop through each player ────────────────────────────────────────
    for i, row in enumerate(data_rows):
        if not any(row):  # skip empty rows
            continue

        player_id  = row[0]
        name       = row[1]
        match      = row[2]
        match_id   = row[3]
        agent_type = row[4].strip().upper()

        print(f"\n[{i+1}/{len(data_rows)}] Processing {player_id} - {name}...")

        # Build user_input
        if agent_type == "OVERALL":
            user_input = "pick overall 11"
        elif agent_type == "ECO":
            user_input = "pick eco 11"
        else:
            user_input = "pick form 11"

        # ── 4. Call the router ─────────────────────────────────────────────
        try:
            response = fantasy_team_router(user_input)
        except Exception as e:
            response = f"ERROR: {e}"
        keywords = ["No matches", "scheduled for later"]

        if any(word in str(response) for word in keywords):
                print(f"🛑 STOPPING: {response}")
                # Optional: You can still write this one error row so you know why it stopped
                rows_to_write.append([player_id, "System", response, "N/A"])
                break
        # ── 5. Determine final agent_type label ────────────────────────────
        if any(word in user_input for word in ["best", "overall", "merge", "both"]):
            final_agent_type = "Overall-Scout"
        elif "eco" in user_input:
            final_agent_type = "Eco-Scout"
        else:
            final_agent_type = "Form-Scout"

        print(f"✅ Player {player_id} | {final_agent_type} | Match {match_id}")

        rows_to_write.append([player_id, final_agent_type, response, match_id])

        # ── 6. Sleep between players (skip on last player) ─────────────────
        if i < len(data_rows) - 1:
            print("⏳ Waiting 5 seconds before next player...")
            time.sleep(5)

    # ── 7. Write all rows at once ──────────────────────────────────────────
    if rows_to_write:
        print("\n🔄 Preparing final write... Refreshing Sheet connection.")
        # 1. Re-open the spreadsheet using your existing config/client
        # This handles the "SSL EOF" or "Connection Closed" error
        temp_spreadsheet = client.open(spreadsheet_name)
        response_sheet = temp_spreadsheet.worksheet("Agent_Response")
        response_sheet.insert_rows(rows_to_write, 2)
        print(f"\n🎉 Done! Stored responses for {len(rows_to_write)} players.")
    else:
        print("⚠️ No players found in Player_agent sheet.")

    print("💾 Router finishing: Syncing cache to GCS...")
    config.save_to_gcs()
def update_validator_response():
    """
    Fetches match_id from Agent_Response sheet, runs the Validator Agent,
    and saves the leaderboard to the Validator_Agent sheet.
    """
    try:
        # 1. Load Match_ID from Agent_Response sheet
        response_sheet = spreadsheet.worksheet("Agent_Response")
        all_values = response_sheet.get_all_values()
        data_rows = all_values[1:]  # skip header

        match_id = None
        for row in data_rows:
            if any(row) and len(row) > 3 and row[3].strip():
                match_id = str(row[3]).strip()
                break

        if not match_id:
            print("⚠️ No valid Match ID found in Agent_Response sheet.")
            return

        print(f"✅ Match ID loaded from sheet: {match_id}")

        # 2. Run Validator Agent
        user_input = f"Validate the performance for match_id {match_id}."

        # We assume validator_agent is initialized globally or via create_validator_agent()
        validator_agent=create_validator_agent()
        response = validator_agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]}
        )

        # 3. Extract and Parse the String from the Agent Response
        if "messages" in response and len(response["messages"]) > 0:
            final_message = response["messages"][-1]

            print(final_message)





    except Exception as outer_e:
        print(f"❌ Error in update_validator_response: {outer_e}")
def update_todays_matches():
    """
    Calls the Master Router to fetch and sync today's matches.
    This is typically called at 7:00 AM.
    """
    print("🌅 Starting Daily Match Sync...")

    # 1. Define the trigger input for the router
    user_input = "What is today's match"

    try:
        # 2. Call the master router (from agents.router)
        # The router will see 'today' and trigger get_started_matches_report
        response = fantasy_team_router(user_input)

        # 3. Log the result
        print("-" * 30)
        print(f"🤖 Router Response:\n{response}")
        print("-" * 30)

        if "No matches" in str(response):
            print("📅 Sync complete: No matches scheduled for today.")
        else:
            print("✅ Sync complete: Today's matches are loaded and ready.")

        return response

    except Exception as e:
        print(f"❌ Error during match sync: {e}")
        return f"Error: {e}"
if __name__ == "__main__":
    update_agent_responses()