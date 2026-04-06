import os
import uvicorn
from fastapi import FastAPI, BackgroundTasks, HTTPException, Query
from fastapi.responses import JSONResponse

# --- IMPORT YOUR AGENT LOGIC ---
# This assumes your functions are named exactly like this in agents.py
try:
    from agents import update_agent_responses, fantasy_team_router
except ImportError as e:
    print(f"❌ Error importing from agents.py: {e}")
    raise

app = FastAPI(title="Fantasy Cricket AI Service")

# 1. HEALTH CHECK (To see if the server is up)
@app.get("/")
def home():
    return {
        "status": "online",
        "service": "Fantasy AI Agent",
        "endpoints": ["/run-daily-sync (POST)", "/chat (GET)"]
    }

@app.post("/sync-matches")
async def sync_matches_only(background_tasks: BackgroundTasks):
    from agents import load_stored_matches
    background_tasks.add_task(load_stored_matches)
    return {"message": "Morning Match Sync Started!"}

@app.post("/run-scouts")
async def run_scout_loop(background_tasks: BackgroundTasks):
    from agents import update_agent_responses
    background_tasks.add_task(update_agent_responses)
    return {"message": "Evening Scout Loop Started!"}
# 3. THE LIVE CHATBOT TRIGGER (Google Chat / Apps Script)
@app.get("/chat")
async def chat_endpoint(query: str = Query(..., description="The user's question")):
    """
    Provides an instant response for the Google Chat Bot.
    """
    print(f"💬 Received Chat Query: {query}")
    try:
        # Calls your router logic (Form, Eco, or Overall)
        response_text = fantasy_team_router(query)
        return {"response": response_text}
    except Exception as e:
        print(f"❌ Error in fantasy_team_router: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- FOR LOCAL TESTING ---
if __name__ == "__main__":
    # In Cloud Run, the PORT environment variable is set automatically.
    # Locally, it defaults to 8000.
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)