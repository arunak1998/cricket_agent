# AI Agent Instructions for Cricket Fantasy Agent Project

## Project Overview

This is a **LangChain-based multi-agent system** for generating optimal fantasy cricket teams (XI) using AI reasoning over real-time cricket data, weather, and venue intelligence. The system uses modular Python code structure with an automated scheduler that fetches matches at 7 AM and monitors them every 5 minutes, auto-triggering agents when matches start.

**Core Technology:**
- **LLM:** Groq (gpt-4-oss-120b model)
- **Framework:** LangChain 1.2.7+ with LangGraph state machines
- **Implementation:** Python 3.12+ in modular `src/agents/` package
- **Data:** JSON-based caching (`cricket_cache.json`, `daily_matches.json`, `match_history.json`)
- **Testing:** Comprehensive test suite in `src/tests/` with expected output examples

---

## Architecture Essentials

### Triple-Agent Hierarchy

The system uses a **supervisor pattern** with three specialized agents:

1. **Eco-Scout Agent** - Selects XI based on environmental factors (weather, pitch, venue)
   - Tools: `get_match_venue()` → `get_cricket_squads_by_match()` → `get__weathr()` → `get_match_environment()`
   - Key Logic: Favors batting/bowling specialists based on pitch conditions
   - Output: 11-player team with environment-based reasoning

2. **Form-Scout Agent** - Selects XI based on current player momentum
   - Tools: `get_match_venue()` → `get_cricket_squads_by_match()` → `get_batch_player_stats()`
   - Key Logic: Prioritizes recent T20 form (SR > 140), wicket-taking records, venue alignment
   - Output: 11-player balanced team with form analysis

3. **Supervisor Agent** - Routes user queries to appropriate specialist agent
   - Decision Logic: Analyzes user intent ("Eco-Scout XI" vs "Form-Scout XI")
   - Delegates execution while maintaining conversation context

**State Graph Pattern:** Uses LangGraph's `StateGraph` with tool-calling nodes. Each agent returns structured JSON with exactly 11 players.

---

## Critical Data Structures

All data uses **Pydantic models** for validation (defined in [src/agents/models.py](src/agents/models.py)):

```python
class FantasyPlayer(BaseModel):
    player_id: str
    name: str
    team: str
    role: str  # "Batter", "Bowler", "Wicket-Keeper", "All-rounder"
    recent_form: Optional[dict]  # T20 stats: {"balls": int, "runs": int, "wickets": int, "strike_rate": float}
    venue_alignment: Optional[float]  # 0.0-1.0 match suitability
    selection_reason: str  # Why this player was selected

class FantasyTeam(BaseModel):
    timestamp: str  # ISO format
    match: str  # "Team A vs Team B"
    match_id: str
    agent_type: str  # "Eco-Scout" or "Form-Scout"
    players: List[FantasyPlayer]  # Exactly 11 players
    selection_logic: str  # Overall team reasoning
    constraints_validation: dict  # Validation status of mandatory constraints
```

**Mandatory Constraints (apply to BOTH agents):**
- Exactly **11 players total**
- **1 Wicket-Keeper** (highest recent runs)
- **4 Bowlers** (top wicket-takers OR best bowling form)
- **6 Batsmen/All-rounders** (mixed based on venue/form)

---

## Project Structure - Modular Architecture

```
agent_project/
├── src/                              # Main source code (modular Python packages)
│   ├── agents/                       # Agent system package
│   │   ├── __init__.py              # Package exports
│   │   ├── models.py                # Pydantic models (FantasyPlayer, FantasyTeam)
│   │   ├── cache.py                 # CacheManager, MatchStorage, ProcessingHistory
│   │   ├── base.py                  # Setup functions, LLM initialization
│   │   ├── tools.py                 # Tool definitions (get_match_venue, etc.)
│   │   ├── eco_scout.py             # Eco-Scout agent (environment-based selection)
│   │   ├── form_scout.py            # Form-Scout agent (form-based selection)
│   │   └── supervisor.py            # Supervisor agent (routing logic)
│   ├── utils/                       # Utility modules (schedulers, helpers)
│   ├── tests/                       # Test suite with expected outputs
│   │   └── test_agents.py          # Comprehensive tests with output examples
│   └── __init__.py                 # Package initialization
├── notebooks1/                      # Legacy Jupyter notebooks
│   ├── agents.ipynb                # Original implementation (reference)
│   ├── agent2.ipynb, agent3.ipynb  # Experimental variations
│   └── cricket_cache.json          # Persisted cache data
├── main.py                         # CLI entry point (uses src/ modules)
├── pyproject.toml                  # Dependencies & project metadata
├── README.md                       # User documentation
└── .github/
    └── copilot-instructions.md    # This file
```

## Key Files Summary

| File | Purpose | Key Classes/Functions |
|------|---------|---|
| [src/agents/models.py](src/agents/models.py) | Data validation | `FantasyPlayer`, `FantasyTeam` |
| [src/agents/cache.py](src/agents/cache.py) | Persistent storage | `CacheManager`, `MatchStorage`, `ProcessingHistory` |
| [src/agents/base.py](src/agents/base.py) | Initialization | `setup_lm()`, `setup_cache()`, `get_api_headers()` |
| [src/agents/tools.py](src/agents/tools.py) | Tool definitions | `get_match_venue()`, `get_cricket_squads_by_match()`, `get_batch_player_stats()`, `get__weathr()`, `get_match_environment()` |
| [src/agents/eco_scout.py](src/agents/eco_scout.py) | Environment agent | `create_eco_scout_agent()` |
| [src/agents/form_scout.py](src/agents/form_scout.py) | Form agent | `create_form_scout_agent()` |
| [src/agents/supervisor.py](src/agents/supervisor.py) | Router agent | `create_supervisor_agent()` |
| [src/tests/test_agents.py](src/tests/test_agents.py) | Test suite | `test_models()`, `test_cache_manager()`, `test_complete_workflow()` |
| [notebooks1/agents.ipynb](notebooks1/agents.ipynb) | Original notebook | Reference implementation (deprecated for production) |

---

## Workflow: Scheduling + Agent Invocation

### Automated Flow (No Human Intervention)

```
7:00 AM Daily → fetch_morning_matches()
    ↓ Stores matches in daily_matches.json
Every 5 min → monitor_matches_for_start()
    ↓ Polls Cricbuzz API for status changes
Match LIVE → invoke_agent_for_match(match_id)
    ↓ Supervisor routes to Eco-Scout or Form-Scout
    ↓ Calls tools sequentially OR in parallel
    ↓ LLM reasons across returned data
    ↓ Selects 11-player team with constraints
Result → JSON stored, match marked processed
```

**Key Implementation Details:**
- Matches stored in `daily_matches.json` with structure: `{"timestamp": "...", "matches": [{id, name, venue, status}]}`
- Processing history in `match_history.json`: `{"processed_matches": [match_ids]}`
- **No duplicate processing:** Always check `match_history.json` before invoking agents
- Scheduler uses `schedule` library (not APScheduler); runs in background thread

---

## API Integration Patterns

### Cricbuzz RapidAPI
**Rate Limits:** Depends on subscription tier; implement delays when needed.

**Endpoints Used:**
- `GET /matches/v1/upcoming` → Today's match list
- `GET /mcenter/v1/{match_id}` → Match details + status
- `GET /mcenter/v1/{match_id}/team/{team_id}` → Playing XI (role-based grouping)
- `GET /stats/v1/player/{player_id}` → T20 recent stats (balls, runs, wickets)

**Implementation Pattern:**
```python
headers = {"x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
           "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"}
response = requests.get(url, headers=headers)
# Always validate response.status_code before parsing JSON
```

### Caching Strategy
- **CacheManager class** in [src/agents/cache.py](src/agents/cache.py) tracks cached data by key (e.g., `"venue_team_a_vs_team_b"`, `"squad_match_123"`)
- **Avoid redundant API calls** within same agent execution
- Persist cache to `cricket_cache.json` after each agent run
- **Cache TTL:** Not explicitly set; assumes within-session reuse only

### Other APIs
- **Visual Crossing Weather:** City + date → temperature, rainfall, conditions
- **Tavily Search:** Venue name → stadium history, pitch reports (for context/reasoning)

---

## Common Developer Patterns

### Adding a New Tool

```python
from langchain.tools import tool
from .cache import CacheManager

@tool
def my_tool_name(match: str, team: str) -> str:
    """Concise docstring explaining what this returns."""
    cache = CacheManager()
    cache_key = f"my_tool_{match}_{team}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    # Fetch data from API
    # Cache result
    result = f"Insight: {data}"
    cache.set(cache_key, result)
    return result

# Register in tool list:
eco_agent_tools = [get_match_venue, get_cricket_squads_by_match, my_tool_name]
```

**Tool Design Rules:**
- Return **formatted strings** (not raw JSON) for readability in agent reasoning
- Include error handling: try-catch + log errors, return fallback message
- Use `cache.get(key)` before API calls; cache results with `cache.set(key, value)`
- Document expected return format in docstring

### Extending Agent Logic

Edit **system_prompt** in agent files ([src/agents/eco_scout.py](src/agents/eco_scout.py) or [src/agents/form_scout.py](src/agents/form_scout.py)) to:
- Add new selection criteria (e.g., "prefer all-rounders on high-scoring venues")
- Adjust player type distribution ("5 bowlers instead of 4" for spin tracks)
- Add reasoning constraints ("never pick injured players" → requires new tool)

**Example modification:**
```python
ECO_SCOUT_SYSTEM_PROMPT = """You are Eco-Scout. Select a balanced 11:
- 1 Wicket-Keeper (highest runs in recent fast-bowling conditions)
- 4 Bowlers (best suited to pitch conditions)
- 6 Batsmen/AR (prefer aggressive on short-boundary venues)
...
```

---

## Testing Comprehensive Examples

Run tests from [src/tests/test_agents.py](src/tests/test_agents.py):

```bash
# Run all tests
python -m pytest src/tests/test_agents.py -v

# Run specific test
python -m pytest src/tests/test_agents.py::test_models -v
```

**Test Individual Tools:**
```python
from src.agents.tools import get_match_venue, get_cricket_squads_by_match
from src.agents.base import setup_cache

cache = setup_cache()

# Test venue tool
result = get_match_venue("India vs Pakistan")
# Expected output:
# "Venue: MCG, City: Melbourne"

# Test squads tool
squads = get_cricket_squads_by_match("India vs Pakistan")
# Expected output format:
# "--- India Squad ---
#  - Virat Kohli (Batter) [ID: 12345]
#  - Jasprit Bumrah (Bowler) [ID: 12346]
#  --- Pakistan Squad ---
#  - Babar Azam (Batter) [ID: 23456]"
```

**Test Agent Model Validation:**
```python
from src.agents.models import FantasyPlayer, FantasyTeam

# Create player
player = FantasyPlayer(
    player_id="9443",
    name="Tim Seifert",
    team="New Zealand",
    role="Wicket-Keeper",
    recent_form={"balls": 45, "runs": 156, "wickets": 0, "strike_rate": 146.67},
    venue_alignment=0.85,
    selection_reason="Recent SR 146.67 with excellent form"
)

# Create team (must have exactly 11 players)
team = FantasyTeam(
    match="India vs Pakistan",
    match_id="139186",
    agent_type="Form-Scout",
    players=[player] * 11,
    selection_logic="Prioritized recent T20 form (SR > 140)"
)

# Validate constraints
team.validate_constraints()
# Returns: {"total_players": True, "wicket_keepers": True, "bowlers": True, "batters_and_all_rounders": True}
```

**Expected Eco-Scout Output Example:**
```json
{
  "timestamp": "2026-02-18T14:30:00",
  "match": "India vs Pakistan",
  "match_id": "139186",
  "agent_type": "Eco-Scout",
  "selection_logic": "Environmental analysis: MCG pitch is fast & bouncy (favors pace bowlers). Temperature 28°C, partly cloudy - hot conditions favor aggressive batters. Selected 4 pace bowlers for early wickets, 6 aggressive batters for short boundaries.",
  "players": [
    {
      "player_id": "9443",
      "name": "Tim Seifert",
      "team": "NZ",
      "role": "Wicket-Keeper",
      "recent_form": {"strike_rate": 146.67},
      "venue_alignment": 0.85,
      "selection_reason": "Strong form on bowling-friendly pitches, good against pace"
    }
  ],
  "constraints_validation": {
    "total_players": true,
    "wicket_keepers": true,
    "bowlers": true,
    "batters_and_all_rounders": true
  }
}
```

**Expected Form-Scout Output Example:**
```json
{
  "timestamp": "2026-02-18T14:30:00",
  "match": "India vs Pakistan",
  "match_id": "139186",
  "agent_type": "Form-Scout",
  "selection_logic": "Form-based selection: Prioritized T20 strike rates > 140. Selected Virat Kohli (SR 142.7, 287 runs in 5 games), Hardik Pandya (SR 151.2). Top 4 bowlers: Bumrah (6 wickets), Afridi (5 wickets), Cummins (5 wickets), Khan (4 wickets).",
  "players": [
    {
      "player_id": "12345",
      "name": "Virat Kohli",
      "team": "India",
      "role": "Batter",
      "recent_form": {"balls": 89, "runs": 287, "strike_rate": 142.70},
      "venue_alignment": 0.82,
      "selection_reason": "Peak form: SR 142.7, 3 consecutive 50+ scores, consistent performer"
    }
  ],
  "constraints_validation": {
    "total_players": true,
    "wicket_keepers": true,
    "bowlers": true,
    "batters_and_all_rounders": true
  }
}
```

**Test Full Supervisor Routing:**
```python
from src.agents.supervisor import create_supervisor_agent
from src.agents.base import setup_lm

model = setup_lm()
supervisor = create_supervisor_agent(model)

# Test routing (environment keywords → Eco-Scout)
result = supervisor.invoke({
    "messages": [{"role": "user", "content": "Pick XI for India vs Pakistan considering weather and pitch"}]
})
# Expected: agent_choice = "Eco-Scout"

# Test routing (form keywords → Form-Scout)
result = supervisor.invoke({
    "messages": [{"role": "user", "content": "Pick XI based on recent form and strike rates"}]
})
# Expected: agent_choice = "Form-Scout"
```

---

## Environment & Dependencies

### Required Environment Variables (`.env`)
```env
GROQ_API_KEY=your_key
TAVILY_API_KEY=your_key
RAPIDAPI_KEY=your_key
WEATHER_API_KEY=your_key
GOOGLE_API_KEY=optional_fallback_key
```

### Key Dependencies
- `langchain>=1.2.7` - Agent framework + LLM abstraction
- `langchain-groq>=1.1.1` - Groq provider integration
- `langchain-tavily>=0.2.17` - Tavily search tool
- `schedule>=1.2.2` - Job scheduling (7 AM fetch, 5-min monitor)
- `python-dotenv>=1.2.1` - Environment variable loading
- `pydantic>=2.0` - Data validation

### Virtual Environment
```bash
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

---

## Common Pitfalls & Solutions

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| Agent outputs 9/10 players | Constraint logic incomplete | Verify system prompt + `len(team) == 11` validation |
| "Duplicate processing" error | `match_history.json` not checked | Always load history before invoking agents |
| API rate limit exceeded | No delays between requests | Add `time.sleep(0.5)` between Cricbuzz calls |
| Cache not persisting | `cache.save()` not called | Call after agent run: `cache.save(CACHE_FILE)` |
| Import errors from src/ | Python path not set | Run from project root: `python -m src.agents.base` |
| Pydantic validation fails | Role name mismatch | Use exact values: `"Batter"`, `"Bowler"`, `"Wicket-Keeper"`, `"All-rounder"` |

---

## Project-Specific Conventions

1. **Player Role Mapping:** Always normalize roles from API to: `"Batter"`, `"Bowler"`, `"Wicket-Keeper"`, `"All-rounder"` (case-sensitive)
2. **Match Naming:** Use `"Team A vs Team B"` format for consistency (matches API responses)
3. **Logging:** Use `logger.info()`, `logger.error()` (configured in [src/agents/base.py](src/agents/base.py))
4. **JSON Keys:** Use snake_case for cache keys (`"venue_india_vs_pakistan"`, not camelCase)
5. **Tool Order:** Within agents, call venue → squads → stats tools first, then reasoning tools (weather, environment) last for optimal data flow
6. **Output Format:** All agent outputs must be valid JSON with exactly 11 players and constraint validation

---

## Useful Development Commands

```python
# Quick test from Python shell
from src.agents.base import setup_lm, setup_cache
from src.agents.supervisor import create_supervisor_agent

model = setup_lm()
supervisor = create_supervisor_agent(model)

# Test supervisor routing
result = supervisor.invoke({
    "messages": [{"role": "user", "content": "Pick XI considering weather and pitch"}]
})
print(result["agent_choice"])  # Should print "Eco-Scout"
```

---

## When to Ask for Clarification

- **Ambiguous match names:** Ask user for date/venue if "India vs Pakistan" matches multiple upcoming games
- **Missing API keys:** Halt and request required environment variables
- **Conflicting agent strategies:** Confirm which agent (Eco-Scout vs Form-Scout) user prefers before invocation
- **Data inconsistencies:** If API returns conflicting player roles, log and ask for manual verification
- **Import/Path Issues:** Verify working directory is project root
