# 🏏 Cricket Fantasy Agent - Intelligent Playing XI Generator

An AI-powered system that generates optimal fantasy cricket playing XI (11-player teams) using LangChain agents with real-time data from Cricbuzz APIs, weather forecasts, and venue intelligence.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Architecture](#project-architecture)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Scheduler System](#scheduler-system)
- [API Integration](#api-integration)
- [Development Workflow](#development-workflow)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

This project leverages **LLM-powered agents** to intelligently select fantasy cricket teams based on:

- **Environmental Factors** (Eco-Scout Agent)
  - Weather conditions (temperature, rainfall)
  - Pitch characteristics (batting-friendly vs bowling-friendly)
  - Venue history and scoring patterns
  - Stadium records and statistics

- **Player Performance** (Form-Scout Agent)
  - Recent T20 strike rates and batting averages
  - Recent bowling figures and wicket-taking records
  - Player momentum and current form
  - Venue-specific player performance alignment

The system automatically monitors cricket matches and invokes the appropriate agent when matches start, using a daily scheduler that fetches match data at 7 AM.

---

## ✨ Features

### Core Functionality
- ✅ **Dual Agent System**: Eco-Scout and Form-Scout agents for different selection strategies
- ✅ **Automatic Match Monitoring**: Fetches matches at 7 AM, monitors status throughout the day
- ✅ **Agent Auto-Trigger**: Automatically invokes agent when a match starts
- ✅ **Duplicate Prevention**: Tracks processed matches to avoid redundant runs
- ✅ **Caching System**: Stores match data, squads, and player statistics

### Data Integration
- ✅ **Live Cricket API**: Cricbuzz RapidAPI for match, squad, and player data
- ✅ **Weather Integration**: Visual Crossing Weather API for match-day weather
- ✅ **Search Capability**: Tavily Search for venue information and pitch reports
- ✅ **Real-time Updates**: Monitors match status continuously

### Output
- ✅ **Structured Fantasy XI**: 11-player team with roles and selection logic
- ✅ **Environmental Reasoning**: Explanation of how environmental factors influenced selection
- ✅ **Form Analysis**: Player momentum and performance metrics
- ✅ **JSON Storage**: Persistent storage of matches and processing history

---

## 🛠 Technology Stack

### Core Framework
- **Python** 3.12+
- **LangChain** 1.2.7+ - Build agentic AI systems
- **Groq** - LLM Provider (OpenAI GPT-OSS-120B model)

### APIs & Services
- **Cricbuzz Cricket API** (RapidAPI) - Cricket data, matches, squads, player stats
- **Tavily Search** - Venue information and pitch reports
- **Visual Crossing Weather API** - Weather forecasts
- **Google Generative AI** - Optional alternative LLM provider
- **LangChain Tavily** - Search integration

### Utilities
- **python-dotenv** 1.2.1+ - Environment variable management
- **requests** - HTTP client for API calls
- **schedule** - Job scheduling for automated tasks
- **json** - Data persistence
- **logging** - Application logging

### Development Tools
- **UV** - Fast Python package manager
- **Python Virtual Environment** (.venv)

---

## 🏗 Project Architecture

```
┌─────────────────────────────────────────────────────────┐
│        Cricket Fantasy Agent System                      │
└─────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐      ┌──────▼──────┐    ┌─────▼─────┐
   │ 7 AM    │      │ Every 5 Min │    │   Agent   │
   │ Fetch   │      │ Monitor     │    │ Invocation│
   │ Matches │      │ Status      │    │           │
   └────┬────┘      └──────┬──────┘    └─────┬─────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                  ┌────────▼────────┐
                  │ Match Storage   │
                  │ daily_matches   │
                  │ match_history   │
                  └────────┬────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼──────┐    ┌──────▼──────┐   ┌──────▼──────┐
   │ Cricbuzz  │    │   Weather   │   │   Tavily    │
   │ API       │    │   API       │   │   Search    │
   └───────────┘    └─────────────┘   └─────────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                  ┌────────▼────────┐
                  │ LLM Agent       │
                  │ (Eco-Scout or   │
                  │  Form-Scout)    │
                  └────────┬────────┘
                           │
                  ┌────────▼────────┐
                  │ Fantasy XI      │
                  │ Output          │
                  └─────────────────┘
```

### Data Flow

1. **Morning (7:00 AM)**: `fetch_morning_matches()` → Stores matches in `daily_matches.json`
2. **Throughout Day (Every 5 min)**: `monitor_matches_for_start()` → Checks match status
3. **Match Starts**: If status = "live" → `invoke_agent_for_match()` triggers
4. **Agent Execution**: Tools fetch squads, weather, pitch → LLM selects XI
5. **Result Storage**: Match marked as processed in `match_history.json`

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12 or higher
- API Keys:
  - **Cricbuzz RapidAPI**: [Sign up here](https://rapidapi.com/cricapi/api/cricbuzz-cricket)
  - **Groq API**: [Get key here](https://console.groq.com)
  - **Tavily API**: [Get key here](https://tavily.com)
  - **Google API** (optional): [Get key here](https://makersuite.google.com)
  - **Visual Crossing Weather**: [Sign up here](https://www.visualcrossing.com)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd agent_project
   ```

2. **Create Python virtual environment**
   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   # OR with UV
   uv pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```

5. **Add your API keys to `.env`**
   ```env
   GROQ_API_KEY=your_groq_key_here
   TAVILY_API_KEY=your_tavily_key_here
   GOOGLE_API_KEY=your_google_key_here
   RAPIDAPI_KEY=your_cricbuzz_key_here
   WEATHER_API_KEY=your_weather_key_here
   ```

---

## 📁 Project Structure

```
agent_project/
├── main.py                          # Entry point
├── pyproject.toml                   # Project metadata & dependencies
├── README.md                        # Project documentation
├── .env                             # Environment variables (create locally)
├── .env.example                     # Environment variables template
├── notebooks1/
│   ├── agents.ipynb                 # Main agent implementation
│   ├── cricket_cache.json           # Cached player/venue data
│   └── [other notebooks]
├── daily_matches.json               # Today's matches (created at 7 AM)
├── match_history.json               # Processed matches log
├── app.log                          # Application logs
└── .github/
    └── prompts/
        └── readme-blueprint-generator.prompt.md
```

### Key Files

- **agents.ipynb**: Core implementation
  - Agent initialized with Groq LLM
  - Tool definitions (venue, squads, player stats, weather)
  - Scheduler functions
  - Match monitoring and agent invocation

- **main.py**: Entry point for CLI

- **pyproject.toml**: Dependencies and project configuration

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# LLM Provider
GROQ_API_KEY=your_groq_api_key

# APIs
TAVILY_API_KEY=your_tavily_search_key
GOOGLE_API_KEY=your_google_genai_key
RAPIDAPI_KEY=your_cricbuzz_rapidapi_key
WEATHER_API_KEY=your_visual_crossing_key

# Optional: Alternative model providers
# ANTHROPIC_API_KEY=your_anthropic_key
# OPENAI_API_KEY=your_openai_key
```

### Scheduler Configuration

Edit in notebook:

```python
# Morning fetch time
schedule.every().day.at("07:00").do(fetch_morning_matches)

# Monitor interval
schedule.every(5).minutes.do(monitor_matches_for_start)
```

---

## 📅 Scheduler System

### Workflow

```
┌─────────────────────────────────────────┐
│ 7:00 AM - Fetch Daily Matches           │
│ ✓ Calls get_todays_match_list()         │
│ ✓ Stores in daily_matches.json          │
│ ✓ Runs ONLY once per day                │
└──────────┬──────────────────────────────┘
           │
┌──────────▼──────────────────────────────┐
│ Every 5 Minutes - Monitor Match Status  │
│ ✓ Check if match has started (LIVE)    │
│ ✓ Load stored matches                  │
│ ✓ For each match:                      │
│   - Poll Cricbuzz API                  │
│   - Detect status change               │
│   - Auto-trigger agent if started      │
└──────────┬──────────────────────────────┘
           │
┌──────────▼──────────────────────────────┐
│ Agent Execution (Once per Match)        │
│ ✓ Invoke appropriate agent              │
│ ✓ Call tools (squads, weather, pitch)  │
│ ✓ Generate fantasy XI                  │
│ ✓ Mark as processed                    │
└─────────────────────────────────────────┘
```

### Manual Commands

```python
# Start automatic scheduler
start_scheduler_background()

# Manual execution
fetch_morning_matches()          # Fetch at 7 AM
monitor_matches_for_start()      # Check status & trigger agent
load_stored_matches()            # View stored matches
```

---

## 🔌 API Integration

### Cricbuzz Cricket API

**Endpoints Used:**
- `GET /matches/v1/upcoming` - Get upcoming matches
- `GET /matches/v1/live` - Get live/current matches
- `GET /mcenter/v1/{match_id}` - Get match details
- `GET /mcenter/v1/{match_id}/team/{team_id}` - Get team squad
- `GET /stats/v1/player/{player_id}` - Get player statistics

**Rate Limits:** Varies by plan - configured with delay mechanisms

### Weather API (Visual Crossing)

**Endpoint:**
```
GET https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city}/{date}
```

**Parameters:**
- `city`: Match venue city
- `date`: Match date (YYYY-MM-DD)
- `unitGroup`: metric
- `key`: API key

### Tavily Search

**Usage:**
- Venue information and stadium history
- Pitch reports and conditions
- Match-day weather conditions

---

## 🤖 Agent System

### Eco-Scout Agent

**Selection Strategy**: Environment-based

**Tool Execution Order:**
1. `get_match_venue()` - Stadium name, city, scoring history
2. `get_cricket_squads_by_match()` - Playing XI for both teams
3. `get__weathr()` - Weather conditions
4. `get_match_environment()` - Pitch report

**Decision Logic:**
- Weather impact on batting/bowling
- Pitch characteristics favor bowlers/batsmen
- Venue average scores
- Player types suitable for conditions

### Form-Scout Agent

**Selection Strategy**: Player momentum-based

**Tool Execution Order:**
1. `get_match_venue()` - Venue context
2. `get_cricket_squads_by_match()` - Squad with player IDs
3. `get_batch_player_stats()` - T20 form for all 22 players

**Decision Logic:**
- Recent strike rates (SR > 140 = form)
- Wicket-taking records
- Venue alignment
- All-rounder value picks

### Roster Constraints

Both agents produce exactly:
- **11 players total**
- **1 Wicket Keeper** (highest recent runs)
- **4 Bowlers** (top 4 wicket-takers / best bowling form)
- **6 Batsmen/All-rounders** (mixed based on venue)

---

## � Complete Call Flow & Architecture

### Execution Phases (From agents.ipynb)

#### Phase 1: System Initialization
**Purpose**: Setup environment and LLM
**Key Calls**:
- `load_dotenv()` - Load environment variables from .env
- `init_chat_model(model='openai/gpt-oss-120b', model_provider="groq")` - Initialize Groq LLM
- `CacheManager()` - Initialize cache for API responses

**Output**: Ready-to-use LLM instance with configured API keys

---

#### Phase 2: Tool Framework Setup
**Purpose**: Import and prepare tool execution framework
**Key Calls**:
- `from langchain.tools import tool` - Import tool decorator
- `TavilySearch()` - Initialize Tavily search client
- `CacheManager.load()` - Load existing cache from `cricket_cache.json`

**Output**: Framework ready for tool definition

---

#### Phase 3: Shared Tool Definitions
**Purpose**: Define 4 reusable tools called by both agents
**Tools Defined**:

1. **`get__weathr(city: str, date: str) -> str`**
   - Calls: Visual Crossing Weather API
   - Returns: Temperature, conditions, description
   - Caching: Stores in `cricket_cache.json` with key `weather_{city}_{date}`
   - Usage: By Eco-Scout only

2. **`get_match_venue(match: str) -> str`**
   - Calls: Tavily Search (query about venue, history, scores)
   - Returns: Stadium name, city, pitch history, scoring patterns
   - Caching: Stores with key `venue_{match}`
   - Usage: By both Eco-Scout and Form-Scout

3. **`get_match_environment(location: str) -> str`**
   - Calls: Tavily Search (query about current pitch conditions)
   - Returns: Pitch report (batting-friendly vs bowling-friendly)
   - Caching: Stores with key `pitch_{location}`
   - Usage: By Eco-Scout only

4. **`get_cricket_squads_by_match(match_query: str) -> str`**
   - Calls: Cricbuzz API `/mcenter/v1/{match_id}/team/{team_id}`
   - Returns: Playing 11 for both teams with player IDs and roles
   - Caching: Stores with key `squad_{match_query}`
   - Usage: By both agents

**Output**: 4 tools ready for agent injection

---

#### Phase 4: Eco-Scout Agent Creation
**Purpose**: Create environment-based selection agent
**Key Components**:

1. **Pydantic Models**
   ```python
   class FantasyPlayer:
       player_id, name, team, role, scout_logic

   class FantasyTeam:
       reasoning_summary, players (exactly 11)
   ```

2. **System Prompt Configuration**
   - Enforces tool-first execution policy
   - Requires all 4 mandatory tools to succeed
   - Drives selection by weather + pitch only (not form)

3. **Agent Creation**
   ```python
   eco_agent_executor = create_agent(
       model=model,
       tools=[get__weathr, get_match_venue, get_match_environment, get_cricket_squads_by_match],
       system_prompt=ECO_SCOUT_SYSTEM_PROMPT,
       response_format=ToolStrategy(FantasyTeam)
   )
   ```

**Tool Execution Order**: venue → weather → environment → squads
**Output**: Eco-Scout agent ready to invoke

---

#### Phase 5: Form-Scout Agent Creation
**Purpose**: Create form-based selection agent
**Key Components**:

1. **Helper Function: `fetch_single_player_stat(player_id)`**
   - Calls: Cricbuzz API `/stats/v1/player/{player_id}`
   - Returns: Player name, role, recent T20 batting (SR, runs), bowling (wickets, avg)
   - Error Handling: Returns error dict if API fails

2. **Batch Tool: `get_batch_player_stats(player_ids: list)`**
   - Calls: `fetch_single_player_stat()` for each of 22 players
   - Caching: Stores individual players with key `player_{player_id}`
   - Returns: All player stats formatted as string
   - Usage: Called once per match

3. **System Prompt**
   - Enforces sequential one-time tool calls (no loops)
   - Drives selection by strike rate (>140), wickets, venue alignment
   - Ranks wicket-keepers by recent runs

4. **Agent Creation**
   ```python
   form_agent_executor = create_agent(
       model=model,
       tools=[get_match_venue, get_cricket_squads_by_match, get_batch_player_stats],
       system_prompt=FORM_SCOUT_SYSTEM_PROMPT,
       response_format=ToolStrategy(FantasyTeam)
   )
   ```

**Tool Execution Order**: venue → squads → batch_player_stats
**Output**: Form-Scout agent ready to invoke

---

#### Phase 6: Match Management Functions
**Purpose**: Fetch and monitor matches for manual/automatic triggering
**Key Functions**:

1. **`get_todays_match_list()`**
   - Calls: Cricbuzz API `/matches/v1/upcoming`
   - Filters: Only ICC Men's T20 World Cup 2026 series, today's date
   - Returns: List of matches with ID, name, venue, status
   - Note: Called by `store_daily_matches()`

2. **`store_daily_matches()`** (Smart Cache)
   - Logic:
     - Check if `daily_matches.json` exists
     - If exists AND timestamp is TODAY → return cached matches (skip API)
     - If missing OR old → call `get_todays_match_list()` → save with timestamp
   - Purpose: Fetch matches **only once per day at 7 AM**
   - Stores: `{"timestamp": "2026-02-17T07:00:00", "matches": [...]}`

3. **`load_stored_matches()`**
   - Reads: `daily_matches.json`
   - Returns: List of matches from cache
   - Purpose: Load matches without API call

4. **`check_match_status(match_id)`**
   - Calls: Cricbuzz API `/mcenter/v1/{match_id}`
   - Checks: `state` (Preview/In Progress/Complete) and `status` (text)
   - Returns: `{"match_started": bool, "state": str, "status": str}`
   - Purpose: Determine if match is LIVE (every 5 minutes)

5. **`check_all_matches()`**
   - Calls: `load_stored_matches()` → `check_match_status()` for each
   - Groups: Separates into `started_matches` and `upcoming_matches`
   - Returns: (started_list, upcoming_list)
   - Purpose: Get overview of all matches

**Output**: Match management system ready for scheduling

---

#### Phase 7: Supervisor Agent with Delegation
**Purpose**: Route user requests to appropriate specialist agent
**Key Components**:

1. **Delegation Tools** (used by Supervisor):

   ```python
   @tool
   def get_started_matches_report() -> str:
       # Calls: store_daily_matches() → check_all_matches()
       # Returns: Formatted report of LIVE matches
       # Purpose: Check if any matches are live before team generation
   ```

   ```python
   @tool
   def call_form_scout(match_details: str) -> str:
       # Input: "Pick the Form-Scout 11 for Team A vs Team B"
       # Calls: form_agent_executor.invoke({messages: [...]})
       # Returns: JSON object with FantasyTeam schema
       # Purpose: Invoke Form-Scout agent from supervisor
   ```

   ```python
   @tool
   def call_eco_scout(match: str) -> str:
       # Input: "Pick the Eco-Scout 11 for Team A vs Team B"
       # Calls: eco_agent_executor.invoke({messages: [...]})
       # Returns: JSON object with FantasyTeam schema
       # Purpose: Invoke Eco-Scout agent from supervisor
   ```

2. **Supervisor System Prompt**
   - Step 1: Call `get_started_matches_report()`
   - Step 2: Route based on user intent:
     - Form-Scout request → `call_form_scout()`
     - Eco-Scout request → `call_eco_scout()`
     - Best Overall → Call both, merge results
   - Step 3: Return final 11 with `player_id` preserved

3. **Supervisor Agent Creation**
   ```python
   supervisor_agent = create_agent(
       model=model,
       tools=[get_started_matches_report, call_form_scout, call_eco_scout]
   )
   ```

**Output**: Supervisor agent ready to orchestrate team generation

---

### Complete Execution Timeline

```
┌─────────────────────────────────────────────────────────┐
│ INITIALIZATION (One-time)                               │
│ Phase 1-2: Load env, init LLM, setup tools frame         │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│ TOOL/AGENT CREATION (One-time)                           │
│ Phase 3-7: Define 4 tools, create 2 agents, setup routs │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│ 7:00 AM MORNING PHASE                                    │
│ store_daily_matches() → Fetches matches, saves to JSON   │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│ EVERY 5 MINUTES                                          │
│ check_all_matches() → Polls Cricbuzz for match status   │
│ Returns: (started_matches, upcoming_matches)            │
└────────────────────────┬────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
   ┌────▼────────┐              ┌────────▼────┐
   │ Match LIVE? │              │Still Preview│
   │   YES       │              │    NO       │
   └────┬────────┘              └─────────────┘
        │
┌───────▼──────────────────────────────────────────────────┐
│ Call Supervisor Agent                                    │
│ Input: User request (Form, Eco, or Both)                │
└───────┬──────────────────────────────────────────────────┘
        │
   ┌────▼─────────────────┐
   │ Supervisor decides:  │
   │ - Form-Scout only    │
   │ - Eco-Scout only     │
   │ - Both + Merge       │
   └────┬─────────────────┘
        │
┌───────┴──────────┬─────────────────────┐
│                  │                     │
│          ┌───────▼────────┐    ┌──────▼───────┐
│          │ Form-Scout     │    │ Eco-Scout    │
│          │ Invocation     │    │ Invocation   │
│          └───────┬────────┘    └──────┬───────┘
│                  │                     │
│          ┌───────▼──────────────────────┐
│          │ 1. get_match_venue()         │
│          │ 2. get_cricket_squads()      │
│          │ 3. get_batch_player_stats()  │
│          │    (Collect 22 player stats) │
│          │ 4. LLM: Select by form       │
│          │ 5. Return 11 (FantasyTeam)   │
│          └───────┬──────────────────────┘
│                  │
│          ┌───────▼──────────────────────┐
│          │ 1. get_match_venue()         │
│          │ 2. get__weathr()             │
│          │ 3. get_match_environment()   │
│          │ 4. get_cricket_squads()      │
│          │ 5. LLM: Select by env        │
│          │ 6. Return 11 (FantasyTeam)   │
│          └───────┬──────────────────────┘
│                  │
│          ┌───────▼──────────────────────┐
│          │ Supervisor Merges if needed  │
│          │ Returns final 11 + reasoning │
│          └───────┬──────────────────────┘
│                  │
└──────────────────┴──────────────────────┘
                   │
            ┌──────▼─────────┐
            │ User gets XI   │
            │ (JSON format)  │
            └────────────────┘
```

---

## �📊 Data Caching

### Storage Files

1. **daily_matches.json**
   ```json
   {
     "timestamp": "2026-02-17T07:00:00",
     "matches": [
       {
         "match": "Team A vs Team B",
         "id": "match_id_123",
         "venue": "Stadium Name",
         "status": "Match will begin at..."
       }
     ]
   }
   ```

2. **match_history.json**
   ```json
   {
     "processed_matches": ["match_id_1", "match_id_2"]
   }
   ```

3. **cricket_cache.json**
   ```json
   {
     "venue_team_a_vs_team_b": "venue_data...",
     "squad_team_a_vs_team_b": "squad_data...",
     "player_12345": {"name": "Player Name", "bat_form": [...]}
   }
   ```

---

## 🔧 Development Workflow

### Code Organization

```python
# 1. Load environment & initialize LLM
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()
model = init_chat_model(model='openai/gpt-oss-120b', model_provider="groq")

# 2. Define tools (agent capabilities)
@tool
def get_match_venue(match: str) -> str:
    """Tool implementation"""
    pass

# 3. Create agent
agent = create_agent(
    model=model,
    tools=[tool1, tool2, tool3],
    system_prompt="""Agent instructions..."""
)

# 4. Setup scheduler
setup_scheduler()
start_scheduler_background()

# 5. Human-in-the-loop execution
user_query = "Pick the Form-Scout 11 for Team A vs Team B..."
agent.stream({"messages": [{"role": "user", "content": user_query}]})
```

### Coding Standards

- **Tool Design**: Each tool should have clear docstrings and single responsibility
- **Error Handling**: Try-catch blocks with informative error messages
- **Logging**: Use Python logging module for debugging
- **Caching**: Implement JSON-based caching for API responses
- **Type Hints**: Use Python type annotations where possible
- **Comments**: Document complex logic and API integrations

### Testing Approach

**Manual Testing:**
```python
# Test individual tools
result = get_match_venue("Team A vs Team B")
print(result)

# Test scheduler
fetch_morning_matches()
monitor_matches_for_start()

# Test agent
invoke_agent_for_match("Team A vs Team B")
```

**Validation:**
- Verify agent produces exactly 11 players
- Check roster constraints (1 WK, 4 bowlers, 6 bat/AR)
- Validate player roles from API
- Confirm no duplicate agent runs

---

## 🚦 Agent Execution Flow

```
User Request (Match Name)
         │
         ▼
    Agent Starts
         │
    ┌────┴────┐
    │          │
 ┌──▼──┐   ┌──▼──┐
 │Tool 1│   │Tool 2│ ... (Sequential or Parallel)
 └──┬──┘   └──┬──┘
    │        │
    └────┬───┘
         ▼
    LLM Reasoning
    (Analyze returned data)
         │
         ▼
    Selection Logic
    (Apply constraints)
         │
         ▼
    Fantasy XI Output
    (Formatted table)
```

---

## 📝 Contributing

### Guidelines

1. **Code Style**
   - Follow PEP 8 guidelines
   - Use meaningful variable names
   - Maximum line length: 100 characters
   - Use docstrings for functions

2. **Tools & Agents**
   - Add new tools as decorated functions with `@tool`
   - Test tools independently before integration
   - Include error handling and validation
   - Document tool parameters and return values

3. **API Integration**
   - Add new API wrappers in separate sections
   - Implement rate limiting where applicable
   - Cache responses when appropriate
   - Handle authentication via environment variables

4. **Testing**
   - Test new features with sample data
   - Verify scheduler tasks work correctly
   - Check agent output constraints (11 players, etc.)
   - Monitor for API errors and edge cases

---

## 📜 License

This project is open source. See LICENSE file for details.

---

## 🤝 Support & Issues

For issues, feature requests, or questions:
1. Check existing documentation
2. Review agent instructions in notebooks
3. Verify API keys and configuration
4. Check logs in `app.log`

---

## 📚 References

- [LangChain Documentation](https://python.langchain.com/)
- [Cricbuzz Cricket API](https://rapidapi.com/cricapi/api/cricbuzz-cricket)
- [Groq API](https://console.groq.com/keys)
- [Tavily Search](https://tavily.com)

---

**Last Updated**: February 17, 2026
**Version**: 0.1.0
**Status**: Active Development
