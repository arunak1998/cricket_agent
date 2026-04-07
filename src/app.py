import os
from fastapi import FastAPI, Query, BackgroundTasks
from main import update_todays_matches, update_agent_responses, update_validator_response,reset_cache_system
from agents.router import fantasy_team_router

app = FastAPI(title="Fantasy Cricket AI Service")

# 1. THE CHATBOT ENDPOINT (GET)
# This is what your Google Apps Script calls
@app.get("/chat")
def chat_endpoint(query: str = Query(..., description="User message from Chat")):
    """
    Direct interface for Google Chat.
    Example: /chat?query=pick overall 11
    """
    print(f"💬 Chat Request: {query}")
    response = fantasy_team_router(query)
    return {"response": response}

# 2. MORNING SYNC: 7:00 AM (POST)
@app.post("/sync-matches")
async def sync_matches(background_tasks: BackgroundTasks):
    """
    Triggers the 7:00 AM match collection.
    Called by Cloud Scheduler.
    """
    background_tasks.add_task(update_todays_matches)
    return {"status": "Processing", "message": "Morning Match Sync Started."}

# 3. EVENING SYNC: SCOUT LOOP (POST)
@app.post("/run-scouts")
async def run_scouts(background_tasks: BackgroundTasks):
    """
    Triggers the bulk AI scouting for all players in the sheet.
    Called by Cloud Scheduler in the evening.
    """
    background_tasks.add_task(update_agent_responses)
    return {"status": "Processing", "message": "Scout Response Loop Started."}

# 4. NIGHT SYNC: LEADERBOARD (POST)
@app.post("/run-audit")
async def run_audit(background_tasks: BackgroundTasks):
    """
    Triggers the Validator Agent to calculate final scores.
    Called by Cloud Scheduler late at night.
    """
    background_tasks.add_task(update_validator_response)
    return {"status": "Processing", "message": "Leaderboard Validation Started."}

# 5. HEALTH CHECK
@app.post("/reset_cache_system")
async def run_scouts(background_tasks: BackgroundTasks):
    """
    Triggers the cache reset and background processing.
    Called by Cloud Scheduler in the evening.
    """
    # This adds the function to the background queue so the API responds immediately
    background_tasks.add_task(reset_cache_system)

    return {
        "status": "Processing",
        "message": "Cache reset initiated. Scout Response Loop Started."
    }
@app.get("/")
def health_check():
    return {"status": "Online", "service": "Fantasy-AI-Core"}

if __name__ == "__main__":
    import uvicorn
    # Cloud Run provides the PORT environment variable
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)