"""
Tools Module: All tools and functions from notebooks organized in one place.
Simple, clean, organized.

Contains:
- Scout Tools (from agents.ipynb): Weather, Venue, Environment, Squads
- Stats Tools (from agent3.ipynb): Match stats, Fantasy points, Leaderboard
"""

import os
import json
import logging
import requests
from typing import Optional, Dict, List, Union
from datetime import datetime
import re
from langchain.tools import tool

from config.config import config
from config.cache_manager import CacheManager
import pytz
IST = pytz.timezone('Asia/Kolkata')
logger = logging.getLogger(__name__)

# Initialize cache
print(config.CACHE_FILE)
cache = CacheManager(config.CACHE_FILE)

# Get API headers
HEADERS = config.HEADERS
print(HEADERS)

# ==========================================
# SCOUT TOOLS (from agents.ipynb)
# ==========================================
def get_active_spreadsheet():
    """
    Checks if the spreadsheet connection is alive.
    If it's dead/timed out, it creates a fresh one.
    """
    import gspread
    from google.auth import default

    try:
        # 1. Try a "Ping" (fetching the title is the fastest check)
        if config.spreadsheet:
            config.spreadsheet.title
            return
    except Exception as e:
        print(f"🔄 Connection lost ({e}). Re-connecting to Google Sheets...")

    # 2. Re-authorize and Re-open if the ping failed or config is None
    try:
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds, _ = default(scopes=scope)
        client = gspread.authorize(creds)
        config.spreadsheet = client.open(config.GOOGLE_SPREADSHEET_NAME)
        config.GOOGLE_SHEETS_ENABLED = True
        print("✅ Re-connection successful.")
        return
    except Exception as final_e:
        print(f"❌ Failed to reconnect: {final_e}")
        config.GOOGLE_SHEETS_ENABLED = False
        return None

def get__weathr(city: str, date: str) -> str:
    """
    Fetch weather for a city on a specific date.

    Args:
        city: City name (e.g., "Chennai")
        date: Date in YYYY-MM-DD format

    Returns:
        Weather details string
    """
    cache_key = f"weather_{city}_{date}"

    try:
        if cache.exists(cache_key):
            cached_value = cache.get(cache_key)
            logger.debug(f"✅ Weather cache hit for {city} on {date}")
            return f"[CACHED] {cached_value}"

        API_KEY = os.getenv('WEATHER_API_KEY')
        if not API_KEY:
            logger.error("❌ WEATHER_API_KEY not configured")
            return "Error: Weather API key not configured. Please set WEATHER_API_KEY in .env"

        url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city}/{date}?unitGroup=metric&key={API_KEY}&contentType=json"
        response = requests.get(url, timeout=10)

        if response.status_code == 401:
            logger.error("❌ Weather API authentication failed (401)")
            return "Error: Weather API authentication failed. Check WEATHER_API_KEY."
        elif response.status_code == 404:
            logger.warning(f"⚠️ Weather data not found for {city} on {date}")
            return f"Weather data not available for {city} on {date}"
        elif response.status_code != 200:
            logger.error(f"❌ Weather API returned status {response.status_code}")
            return f"Error: API returned status code {response.status_code}"

        data = response.json()
        day_data = data.get('days', [{}])[0]
        temp = day_data.get('temp')
        conditions = day_data.get('conditions')
        description = day_data.get('description', 'No description available.')

        result = (f"Weather in {city} on {date}: "
                  f"Temperature: {temp}°C, "
                  f"Conditions: {conditions}. "
                  f"Summary: {description}")

        cache.set(cache_key, result)
        logger.info(f"✅ Weather for {city} retrieved and cached")
        return result

    except requests.Timeout:
        logger.error(f"❌ Weather API request timed out for {city}/{date}")
        return f"Error: Weather API request timed out (10s timeout)"
    except requests.ConnectionError as e:
        logger.error(f"❌ Connection error fetching weather: {e}")
        return f"Error: Connection error to weather service: {str(e)}"
    except requests.RequestException as e:
        logger.error(f"❌ Weather API request failed: {e}")
        return f"Error: Failed to fetch weather data: {str(e)}"
    except Exception as e:
        logger.error(f"❌ Unexpected error fetching weather: {e}")
        return f"Error: {str(e)}"


def get_match_venue(match: str) -> str:
    """
    Fetch venue details for a match.

    Args:
        match: Match name (e.g., "India vs Pakistan")

    Returns:
        Venue information string
    """
    cache_key = f"venue_{match.lower().replace(' ', '_')}"

    try:
        if cache.exists(cache_key):
            cached_value = cache.get(cache_key)
            logger.debug(f"✅ Venue cache hit for {match}")
            return f"[CACHED] {cached_value}"

        # Using Tavily search for venue information
        try:
            from langchain_tavily import TavilySearch
            tavily = TavilySearch()
            query = f"official venue for {match} today, average first innings score T20, pitch type, stadium history"
            result = str(tavily.invoke(query))
        except ImportError:
            logger.warning("⚠️ Tavily not available, using fallback")
            result = f"Venue information for {match} not available (Tavily not configured)"
        except Exception as e:
            logger.warning(f"⚠️ Tavily search failed: {e}")
            result = f"Venue information for {match} not available"

        cache.set(cache_key, result)
        logger.info(f"✅ Venue information cached for {match}")
        return result

    except Exception as e:
        logger.error(f"❌ Error fetching venue for {match}: {e}")
        return f"Error: Failed to fetch venue information: {str(e)}"



def get_match_environment(location: str) -> str:
    """
    Fetch pitch report and conditions for a location.

    Args:
        location: Venue/stadium name

    Returns:
        Pitch conditions and environment string
    """
    cache_key = f"pitch_{location.lower().replace(' ', '_')}"

    try:
        if cache.exists(cache_key):
            cached_value = cache.get(cache_key)
            logger.debug(f"✅ Pitch cache hit for {location}")
            return f"[CACHED] {cached_value}"

        # Using Tavily search for pitch information
        try:
            from langchain_tavily import TavilySearch
            tavily = TavilySearch()
            query = f"pitch report for {location} cricket stadium, current conditions, bowling or batting friendly"
            result = str(tavily.invoke(query))
        except ImportError:
            logger.warning("⚠️ Tavily not available, using fallback")
            result = f"Pitch information for {location} not available (Tavily not configured)"
        except Exception as e:
            logger.warning(f"⚠️ Tavily search failed: {e}")
            result = f"Pitch information for {location} not available"

        cache.set(cache_key, result)
        logger.info(f"✅ Pitch info cached for {location}")
        return result

    except Exception as e:
        logger.error(f"❌ Error fetching pitch info for {location}: {e}")
        return f"Error: Failed to fetch pitch information: {str(e)}"


def get_cricket_squads_by_match(match_id: int) -> str:
    """
    Fetch playing XI and squads for both teams in a match.

    Args:
        match_id: Match ID from Cricbuzz API

    Returns:
        Formatted squad information string
    """
    cache_key = f"squad_match_{match_id}"

    try:
        if cache.exists(cache_key):
            cached_value = cache.get(cache_key)
            logger.debug(f"✅ Squad cache hit for match {match_id}")
            return f"[CACHED] {cached_value}"

        info_url = f"https://cricbuzz-cricket.p.rapidapi.com/mcenter/v1/{match_id}"
        info_res = requests.get(info_url, headers=HEADERS, timeout=10)
        match_data = info_res.json()

        # Initialize dictionary structure
        squad_dict = {
            "match_id": match_id,
            "teams": {
                "team1": {"name": match_data['team1']['teamname'], "id": match_data['team1']['teamid'], "players": []},
                "team2": {"name": match_data['team2']['teamname'], "id": match_data['team2']['teamid'], "players": []}
            }
        }

        # 3. Fetch Squads for both Teams
        for team_key in ["team1", "team2"]:
            t_id = squad_dict["teams"][team_key]["id"]
            squad_url = f"https://cricbuzz-cricket.p.rapidapi.com/mcenter/v1/{match_id}/team/{t_id}"
            squad_res = requests.get(squad_url, headers=HEADERS, timeout=10)
            s_data = squad_res.json()

            for group in s_data.get('player', []):
                if group.get('category') == "playing XI":
                    for p in group.get('player', []):
                        # Append player dict instead of string concatenation
                        squad_dict["teams"][team_key]["players"].append({
                            "id": str(p.get('id')),
                            "name": p.get('name'),
                            "role": p.get('role')
                        })

        # 4. Save to Cache and Return JSON
        cache.set(cache_key, squad_dict)
        return json.dumps(squad_dict, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})


# ==========================================
# STATS TOOLS (from agent3.ipynb)
# ==========================================

@tool
def fetch_match_stats(match_id: str) -> dict:
    """
    Fetches raw scorecard data from the CricBuzz API and organizes it
    into batting and bowling performance maps for fantasy calculation.
    """
    url = f"https://cricbuzz-cricket.p.rapidapi.com/mcenter/v1/{match_id}/scard"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        data = response.json()
        performance_map = {}

        for innings in data.get('scorecard', []):

            # ── Parse Batting ──────────────────────────────────────────────
            for bat in innings.get('batsman', []):
                p_id = str(bat['id'])
                out_desc = bat.get('outdec', "").lower()
                lbw_bowled = 1 if ("lbw" in out_desc or out_desc.startswith("b ")) else 0

                bat_stats = {
                    "name": bat.get('name'),
                    "batting": {
                        "runs":             int(bat.get('runs', 0)),
                        "balls":            int(bat.get('balls', 0)),
                        "fours":            int(bat.get('fours', 0)),
                        "sixes":            int(bat.get('sixes', 0)),
                        "sr":               float(bat.get('strkrate', 0)),
                        "is_out":           out_desc != "not out",
                        "lbw_bowled_victim": lbw_bowled
                    }
                }

                if p_id not in performance_map:
                    performance_map[p_id] = bat_stats
                else:
                    performance_map[p_id]["batting"] = bat_stats["batting"]

            # ── Parse Bowling ──────────────────────────────────────────────
            # Also count LBW/Bowled victims for THIS bowler from batting list
            lbw_bowled_counts = {}
            for bat in innings.get('batsman', []):
                out_desc = bat.get('outdec', "").lower()
                bowler_name = bat.get('bowler', "").strip().lower()
                if "lbw" in out_desc or out_desc.startswith("b "):
                    lbw_bowled_counts[bowler_name] = lbw_bowled_counts.get(bowler_name, 0) + 1

            for bowl in innings.get('bowler', []):
                p_id = str(bowl['id'])
                bowler_name = bowl.get('name', "").strip().lower()

                bowl_stats = {
                    "bowling": {
                        "wickets":        int(bowl.get('wickets', 0)),
                        "overs":          float(bowl.get('overs', 0)),
                        "maidens":        int(bowl.get('maidens', 0)),
                        "runs_conceded":  int(bowl.get('runs', 0)),
                        "econ":           float(bowl.get('economy', 0)),
                        "dots":           int(bowl.get('dots', 0)),
                        "lbw_bowled_count": lbw_bowled_counts.get(bowler_name, 0)  # ✅ Fixed
                    }
                }

                if p_id not in performance_map:
                    performance_map[p_id] = {"name": bowl.get('name'), "bowling": bowl_stats["bowling"]}
                else:
                    performance_map[p_id]["bowling"] = bowl_stats["bowling"]

        return performance_map

    except Exception as e:
        return {"error": str(e)}


def calculate_fantasy_points_2026(p_data: Dict) -> int:
    """
    Calculate fantasy cricket points for a player based on 2026 rules.

    Args:
        p_data: Player data dictionary with stats

    Returns:
        Total fantasy points (int)
    """
    try:
            pts = 0.0

            # ── Batting ───────────────────────────────────────────────────────────────
            if "batting" in p_data:
                bat   = p_data["batting"]
                runs  = int(bat.get('runs', 0))
                balls = int(bat.get('balls', 0))
                fours = int(bat.get('fours', 0))
                sixes = int(bat.get('sixes', 0))
                sr    = float(bat.get('sr', 0))

                pts += runs
                pts += (fours * 1)
                pts += (sixes * 2)

                if runs >= 100:  pts += 16
                elif runs >= 50: pts += 8
                elif runs >= 30: pts += 4

                if runs == 0 and balls > 0:
                    pts -= 2  # Duck penalty

                if balls >= 10:
                    if sr > 170:            pts += 6
                    elif 150 < sr <= 170:   pts += 4
                    elif 130 <= sr <= 150:  pts += 2
                    elif 60 <= sr <= 70:    pts -= 2
                    elif 50 <= sr < 60:     pts -= 4
                    elif sr < 50:           pts -= 6

            # ── Bowling ───────────────────────────────────────────────────────────────
            if "bowling" in p_data:
                bowl            = p_data["bowling"]
                wickets         = int(bowl.get('wickets', 0))
                overs           = float(bowl.get('overs', 0))
                econ            = float(bowl.get('econ', 0))
                maidens         = int(bowl.get('maidens', 0))
                lbw_bowled_count = int(bowl.get('lbw_bowled_count', 0))

                pts += (wickets * 25)
                pts += (lbw_bowled_count * 8)   # LBW/Bowled bonus per victim

                if wickets >= 5:   pts += 16
                elif wickets >= 4: pts += 8
                elif wickets >= 3: pts += 4

                pts += (maidens * 12)

                if overs >= 2.0:
                    if econ < 5:             pts += 6
                    elif 5 <= econ < 6:      pts += 4
                    elif 6 <= econ <= 7:     pts += 2
                    elif 10 <= econ < 11:    pts -= 2
                    elif 11 <= econ <= 12:   pts -= 4
                    elif econ > 12:          pts -= 6

            return int(pts)

    except Exception as e:
        logger.error(f"❌ Error calculating fantasy points: {e}")
        return 0


@tool
def get_user_selections_from_sheet(match_id: str) -> List[Dict]:
    """
    Fetch user team selections from Google Sheet.

    Args:
        match_id: Match ID

    Returns:
        List of selected teams
    """
    try:
        get_active_spreadsheet()
        if not config.GOOGLE_SHEETS_ENABLED:
            logger.warning("⚠️ Google Sheets not enabled")
            return []

        # Placeholder: Would connect to Google Sheets API
        logger.info(f"ℹ️ Would fetch user selections for match {match_id} from Google Sheets")
        sheet = config.spreadsheet.worksheet("Agent_Response")
        all_values = sheet.get_all_values()

        headers    = all_values[0]   # ['Player_id', 'agent_type', 'response', 'Match_id']
        data_rows  = all_values[1:]  # all data rows

        teams = []
        for row in data_rows:
            if not any(row):
                continue

            row_player_id = row[0].strip()
            row_agent     = row[1].strip()
            row_response  = row[2].strip()
            row_match_id  = str(row[3]).strip()

            # ── Filter by match_id ─────────────────────────────────────────
            if row_match_id != str(match_id).strip():
                continue

            players = []

            # ── Parse response: try JSON first ─────────────────────────────
            if row_response.startswith('{'):
                try:
                    parsed = json.loads(row_response)
                    for p in parsed.get("players", []):
                        players.append({
                            "id":   str(p.get("player_id", p.get("id", ""))),
                            "name": p.get("name", "Unknown").replace("\u202f", " ").strip()
                        })
                except json.JSONDecodeError:
                    pass

            # ── Parse response: Pydantic repr style ───────────────────────
            if not players:
                pydantic_matches = re.findall(r"player_id='(\d+)',\s*name='([^']+)'", row_response)
                for p_id, p_name in pydantic_matches:
                    players.append({
                        "id":   p_id,
                        "name": p_name.replace("\u202f", " ").strip()
                    })

            # ── Parse response: Markdown table fallback ────────────────────
            if not players:
                table_matches = re.findall(r"\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|", row_response)
                for p_id, p_name in table_matches:
                    clean_name = p_name.replace("**", "").replace("\u202f", " ").strip()
                    id_search  = re.search(r"\((\d+)\)", clean_name)
                    actual_id  = id_search.group(1) if id_search else p_id
                    final_name = re.sub(r"\s*\(\d+\)", "", clean_name).strip()
                    players.append({"id": actual_id, "name": final_name})

            teams.append({
                "user":    row_player_id,   # Player_ID acts as the user identifier
                "agent":   row_agent,
                "match_id":row_match_id ,
                "players": players
            })

        print(f"✅ Loaded {len(teams)} teams from sheet for match {match_id}")
        return teams

    except Exception as e:
        logger.error(f"❌ Error fetching user selections: {e}")
        return []


@tool
def calculate_leaderboard(match_id: str) -> str:
    """
    Calculate leaderboard for a match based on team performances.

    Args:
        match_id: Match ID

    Returns:
        Formatted leaderboard string
    """
    try:
        logger.info(f"ℹ️ Calculating leaderboard for match {match_id}")

        """
        Master tool: Reads teams from Agent_Response sheet, fetches live match
        stats, calculates fantasy points using 2026 rules, and returns a
        formatted leaderboard ranked by score.
        """
        # Step 1: Get match stats from API
        stats = fetch_match_stats.run(match_id)
        if "error" in stats:
            return f"❌ Error fetching match stats: {stats['error']}"
        print('inside tool call')

        # Step 2: Get user selections from Google Sheet
        teams = get_user_selections_from_sheet.run(match_id)
        if not teams or "error" in teams[0]:
            return f"❌ Error reading sheet: {teams[0].get('error', 'Unknown error')}"


        # Step 3: Calculate scores
        results = []
        for team in teams:
            score = 0
            for p in team['players']:
                p_stats = stats.get(str(p['id']), {})

                score  += calculate_fantasy_points_2026(p_stats)


            results.append({
                "user":  team['user'],
                "agent": team['agent'],
                "match_id":team['match_id'],
                "score": score
            })

        # Step 4: Sort by score descending
        results.sort(key=lambda x: x['score'], reverse=True)

        print(f"✅ Calculated scores for {len(results)} players.")

        rows_to_write = []
        for i, p in enumerate(results, 1):  # 'i' starts at 1

            p['rank'] = i
            rows_to_write.append([
                p.get("rank"),
                p.get("user"),
                p.get("match_id"),
                p.get("agent"),
                p.get("score")
            ])

        # 5. Write to Sheet
        get_active_spreadsheet()
        if not config.GOOGLE_SHEETS_ENABLED:
            logger.warning("⚠️ Google Sheets not enabled")
            return []
        validator_sheet = config.spreadsheet.worksheet("Validator_Agent")
        validator_sheet.batch_clear(["A2:E100"])

        if rows_to_write:
            validator_sheet.insert_rows(rows_to_write, 2)
            print(f"🎉 Successfully stored {len(rows_to_write)} players in Validator_Agent sheet!")
        else:
            print("⚠️ No player data found in the JSON response.")
        top_3 = results[:3]
        print(top_3)

        # Create a clean summary string for the Agent to read
        summary_for_agent = (
            f"SUCCESS: Full leaderboard of {len(results)} players has been synced to the Google Sheet.\n"
            f"Here are the Top 3 performers for your summary:\n"
        )

        for i, p in enumerate(top_3, 1):
            summary_for_agent += f"{i}. Player: {p['user']} | Agent: {p['agent']} | Score: {p['score']}\n"

        # Return this string so the Agent can write its reasoning_summary
        return summary_for_agent

    except Exception as e:
        logger.error(f"❌ Error calculating leaderboard: {e}")
        return f"Error: {str(e)}"


# ==========================================
# PLAYER STATS TOOLS
# ==========================================

def fetch_single_player_stat(player_id: str) -> dict:
    """Helper function to fetch and parse T20 stats for one player with comprehensive error handling."""
    url = f"https://cricbuzz-cricket.p.rapidapi.com/stats/v1/player/{player_id}"

    try:
        if not HEADERS.get('x-rapidapi-key'):
            logger.error(f"❌ RapidAPI key not configured for player {player_id}")
            return {"id": player_id, "error": "API key not configured"}

        response = requests.get(url, headers=HEADERS, timeout=10)

        # Handle specific HTTP status codes
        if response.status_code == 401:
            logger.error(f"❌ Authentication failed for player {player_id}: 401")
            return {"id": player_id, "error": "API authentication failed"}
        elif response.status_code == 403:
            logger.error(f"❌ Access forbidden for player {player_id}: 403")
            return {"id": player_id, "error": "API access forbidden"}
        elif response.status_code == 404:
            logger.warning(f"⚠️ Player {player_id} not found: 404")
            return {"id": player_id, "error": "Player not found in database"}
        elif response.status_code != 200:
            logger.error(f"❌ API error for player {player_id}: {response.status_code}")
            return {"id": player_id, "error": f"API returned {response.status_code}"}

        response.raise_for_status()  # Raise on 4xx/5xx
        player_data = response.json()

    except requests.Timeout:
        logger.error(f"❌ Timeout fetching player {player_id} (10s)")
        return {"id": player_id, "error": "API request timeout"}
    except requests.ConnectionError as e:
        logger.error(f"❌ Connection error for player {player_id}: {e}")
        return {"id": player_id, "error": f"Connection error: {str(e)}"}
    except requests.RequestException as e:
        logger.error(f"❌ Request error for player {player_id}: {e}")
        return {"id": player_id, "error": f"API request failed: {str(e)}"}
    except ValueError as e:
        logger.error(f"❌ Invalid JSON response for player {player_id}: {e}")
        return {"id": player_id, "error": "Invalid JSON response"}
    except Exception as e:
        logger.error(f"❌ Unexpected error fetching player {player_id}: {e}")
        return {"id": player_id, "error": f"Unexpected error: {str(e)}"}

    # Parse player data with error handling
    t20_batting = []
    t20_bowling = []
    player_name = "Unknown"
    player_role = "Unknown"

    try:
        player_name = player_data.get("name", "Unknown")
        player_role = player_data.get("role", "Unknown")

        # Batting Logic with error handling
        try:
            for row in player_data.get('recentBatting', {}).get('rows', []):
                try:
                    vals = row.get('values', [])
                    if len(vals) > 2 and any(fmt in vals[3] for fmt in ["T20", "T20I"]):
                        score_str = vals[1]
                        if "(" in score_str:
                            raw_runs = score_str.split("(")[0]
                            is_not_out = "*" in score_str
                            clean_runs = raw_runs.replace("*", "").strip()
                            runs = int(clean_runs)
                            balls = int(score_str.split("(")[1].replace(")", ""))
                            sr = round((runs / balls) * 100, 2) if balls > 0 else 0
                            t20_batting.append({
        "runs": runs,
        "balls": balls,
        "sr": sr,
        "status": "Not Out" if is_not_out else "Out",
        "score_display": score_str.split("(")[0].strip() # e.g., "45*" or "45"
    })
                except (ValueError, IndexError) as e:
                    logger.warning(f"⚠️ Error parsing batting stats for {player_name} ({player_id}): {e}")
                    continue
        except Exception as e:
            logger.warning(f"⚠️ Error processing batting data for {player_name} ({player_id}): {e}")

        # Bowling Logic with error handling
        try:
            for row in player_data.get('recentBowling', {}).get('rows', []):
                try:
                    vals = row.get('values', [])
                    if len(vals) > 2 and any(fmt in vals[3] for fmt in ["T20", "T20I"]):
                        bowl_str = vals[1]
                        if "-" in bowl_str:
                            wkts = int(bowl_str.split("-")[0])
                            runs = int(bowl_str.split("-")[1])
                            avg = round(runs / wkts, 2) if wkts > 0 else runs
                            t20_bowling.append({"wkts": wkts, "avg": avg,"match_figure": bowl_str})
                except (ValueError, IndexError) as e:
                    logger.warning(f"⚠️ Error parsing bowling stats for {player_name} ({player_id}): {e}")
                    continue
        except Exception as e:
            logger.warning(f"⚠️ Error processing bowling data for {player_name} ({player_id}): {e}")

    except Exception as e:
        logger.error(f"❌ Unexpected error parsing player {player_id} data: {e}")
        return {"id": player_id, "error": f"Data parsing error: {str(e)}"}

    logger.info(f"✅ Player stats parsed: {player_name} ({player_id})")
    return {
        "id": player_id,
        "name": player_name,
        "role": player_role,
        "bat_form": t20_batting,
        "bowl_form": t20_bowling
    }

@tool
def get_batch_player_stats(player_ids: list) -> str:
    """Fetches T20 form for all players with caching. Caches individual players to avoid redundant API calls."""
    batch_results = []
    errors = []
    successful = 0

    try:
        if not player_ids:
            logger.warning("⚠️ No player IDs provided for batch stats fetch")
            return "Error: Empty player ID list provided"

        logger.info(f"📊 Fetching stats for {len(player_ids)} players...")

        for p_id in player_ids:
            try:
                p_key = f"player_{p_id}"

                # Check cache first (no file I/O per player)
                if cache.exists(p_key):
                    try:
                        cached_value = cache.get(p_key)
                        batch_results.append(cached_value['data'])
                        logger.debug(f"✅ Cache hit for player {p_id}")
                        successful += 1
                        continue
                    except Exception as e:
                        logger.warning(f"⚠️ Cache retrieval error for player {p_id}: {e}")

                # Fetch and cache if not available
                player_stats = fetch_single_player_stat(str(p_id))

                # Check for errors in the returned data
                if "error" in player_stats:
                    errors.append(f"Player {p_id}: {player_stats['error']}")
                    logger.warning(f"⚠️ Error for player {p_id}: {player_stats['error']}")
                else:
                    successful += 1

                try:
                    cache.set(p_key, player_stats)  # Auto-saves with timestamp
                except Exception as e:
                    logger.error(f"❌ Failed to cache player {p_id}: {e}")

                batch_results.append(player_stats)

            except Exception as e:
                logger.error(f"❌ Unexpected error processing player {p_id}: {e}")
                errors.append(f"Player {p_id}: {str(e)}")
                batch_results.append({"id": p_id, "error": str(e)})

        logger.info(f"📊 Batch complete: {successful}/{len(player_ids)} successful")

        if errors:
            logger.warning(f"⚠️ {len(errors)} errors encountered: {', '.join(errors[:3])}")

        return str(batch_results)

    except Exception as e:
        logger.error(f"❌ Critical error in batch player stats: {e}")
        return f"Error: Failed to fetch batch player stats: {str(e)}"



# ==========================================
# MATCH MANAGEMENT TOOLS
# ==========================================

def get_todays_match_list() -> List[Dict]:
    """
    Fetch today's cricket matches from Cricbuzz API.
    Filters by target series and today's date.

    Returns:
        List of match dictionaries with id, match, venue, city, status
    """
    url = "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/upcoming"

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)

        if response.status_code != 200:
            logger.error(f"❌ Failed to fetch matches: {response.status_code}")
            return []

        data = response.json()

        # Get today's date
        from datetime import datetime
        today_str = datetime.now().strftime("%b %d")

        matches_today = []
        target_series = "Indian Premier League 2026"

        # Traverse JSON structure
        for match_type_group in data.get('typeMatches', []):
            for series_group in match_type_group.get('seriesMatches', []):
                wrapper = series_group.get('seriesAdWrapper')

                # Filter by series name
                if wrapper and wrapper.get('seriesName') == target_series:
                    for match in wrapper.get('matches', []):
                        match_info = match.get('matchInfo', {})
                        status = match_info.get('status', "")

                        # Check if match is today
                        if today_str in status:
                            team1 = match_info.get('team1', {}).get('teamName')
                            team2 = match_info.get('team2', {}).get('teamName')
                            match_id = match_info.get('matchId')
                            venue = match_info.get('venueInfo', {}).get('ground')
                            city = match_info.get('venueInfo', {}).get('city')

                            matches_today.append({
                                "match": f"{team1} vs {team2}",
                                "id": match_id,
                                "venue": venue,
                                "city": city,
                                "status": status
                            })

        logger.info(f"✅ Found {len(matches_today)} matches for today")
        return matches_today

    except requests.RequestException as e:
        logger.error(f"❌ API request failed: {e}")
        return []
    except Exception as e:
        logger.error(f"❌ Error fetching matches: {e}")
        return []


def load_stored_matches() -> List[Dict]:
    """
    Load matches from Google Sheet. If sheet data is old or missing,
    fetches fresh data from API and updates the sheet.

    Returns:
        List of match dictionaries with id, match, venue, city, status
    """
    try:
        # Check if Google Sheets is available
        get_active_spreadsheet()
        if not config.GOOGLE_SHEETS_ENABLED or config.spreadsheet is None:
            logger.warning("⚠️ Google Sheets not available, fetching from API only")
            return []
        # Get the sheet with match data from config
        sheet = config.spreadsheet.worksheet("Today_Matches")
        current_date = datetime.now().strftime("%Y-%m-%d")

        # 1. Read existing data from the sheet
        all_values = sheet.get_all_values()

        # 2. Check if we need to refresh from API
        # Refresh if: Sheet is empty, ONLY has headers, OR date (Col F) is old
        needs_refresh = False
        if len(all_values) <= 1:
            needs_refresh = True
        else:
            # Check date in Row 2, Column F (index 5)
            last_fetch_date = all_values[1][5] if len(all_values[1]) > 5 else ""
            if last_fetch_date != current_date:
                needs_refresh = True

        # 3. If we need a refresh, call API and save to sheet
        if needs_refresh:
            logger.info(f"🌐 Sheet data missing or old. Fetching fresh matches for {current_date}")
            todays_games = get_todays_match_list()

            if not todays_games:
                logger.warning("⚠️ No matches found from API today")
                return []

            # Format for sheet: [ID, Match, Venue, City, Status, FetchDate]
            formatted_rows = []
            for m in todays_games:
                formatted_rows.append([
                    m.get('id'),
                    m.get('match'),
                    m.get('venue'),
                    m.get('city'),
                    m.get('status'),
                    current_date
                ])

            # Clear and update sheet
            sheet.batch_clear(['A2:F20'])
            sheet.insert_rows(formatted_rows, 2)
            logger.info(f"✅ Sheet updated with {len(formatted_rows)} fresh matches")

            # Re-fetch values to ensure the loop below works on fresh data
            all_values = sheet.get_all_values()

        # 4. Convert sheet data into list of dictionaries
        cached_matches = []
        for row in all_values[1:]:
            if len(row) >= 5:
                cached_matches.append({
                    "id": row[0],
                    "match": row[1],
                    "venue": row[2],
                    "city": row[3],
                    "status": row[4]
                })

        logger.info(f"📦 Returning {len(cached_matches)} matches from sheet")
        return cached_matches

    except Exception as e:
        logger.error(f"❌ Error loading matches from sheet: {e}")
        # Fallback to API
        try:
            matches = get_todays_match_list()
            if matches:
                cache_key = f"daily_matches_{datetime.now().strftime('%Y-%m-%d')}"
                cache.set(cache_key, matches)
            return matches if matches else []
        except Exception as fallback_e:
            logger.error(f"❌ Fallback to API also failed: {fallback_e}")
            return []
def check_match_status(match_id):
    """
    Checks the Google Sheet first. If 'Started' isn't there,
    calls the API and updates the sheet if the status changed.
    """
    get_active_spreadsheet()
    if not config.GOOGLE_SHEETS_ENABLED or config.spreadsheet is None:
            logger.warning("⚠️ Google Sheets not available, fetching from API only")
            return []
        # Get the sheet with match data from config
    sheet = config.spreadsheet.worksheet("Today_Matches")

    all_values = sheet.get_all_values() # Get all rows

    # --- STEP 1: Check the Sheet Cache ---
    match_row_index = -1
    for i, row in enumerate(all_values):
        if i == 0: continue  # Skip header
        if row[0] == str(match_id):  # Column A is Match_ID
            match_row_index = i + 1  # Sheets are 1-indexed
            current_sheet_status = row[4].lower() # Column E is Status

            # If sheet already knows it started, return immediately (No API call!)
            if current_sheet_status == "started":
                print(f"📦 [CACHE] Match {match_id} already marked as Started in Sheet.")
                return {
                    "match_started": True,
                    "state": row[4],
                    "status": "cached"
                }
            break

    # --- STEP 2: Call the API (Only if Cache says not started) ---
    try:
        print(f"🌐 [API] Checking live status for Match {match_id}...")
        url = f"https://cricbuzz-cricket.p.rapidapi.com/mcenter/v1/{match_id}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        data = response.json()

        state = data.get("state", "").lower()
        status = data.get("status", "").lower()

        # Logic to determine if started
        match_started = (
            state in ["in progress", "live", "innings break"] or
            any(word in status for word in ["opt to", "elect to", "lead by", "need", "won by"])
        )

        # Override for finished/preview
        if state in ["preview", "complete"]:
            match_started = False

        # --- STEP 3: Update the Sheet if status is now 'Started' ---
        if match_started and match_row_index != -1:
            # Update Column E (Status) for this specific match row
            sheet.update_cell(match_row_index, 5, "Started")
            print(f"✅ [SHEET UPDATED] Match {match_id} is now LIVE. Status saved.")

        return {
            "match_started": match_started,
            "state": state,
            "status": status
        }

    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return {"match_started": False, "status": "error", "state": "error"}




def check_all_matches() -> tuple:
    """
    Check status of all daily matches.

    Returns:
        Tuple of (started_matches, upcoming_matches) lists
    """
    try:
        matches = load_stored_matches()

        if not matches:
            logger.warning("⚠️ No matches to check")
            return [], []

        logger.info(f"🔍 Checking {len(matches)} matches...")

        started_matches = []
        upcoming_matches = []

        for match in matches:
            match_id = match.get("id")
            match_name = match.get("match")

            status_info = check_match_status(match_id)

            # Attach status to match object
            match["current_status"] = status_info.get("status")
            match["current_state"] = status_info.get("state")

            if status_info.get("match_started"):
                logger.info(f"🎯 MATCH STARTED → {match_name}")
                started_matches.append(match)
            else:
                logger.info(f"⏳ UPCOMING → {match_name}")
                upcoming_matches.append(match)

        return started_matches, upcoming_matches

    except Exception as e:
        logger.error(f"❌ Error checking all matches: {e}")
        return [], []


@tool
def get_started_matches_report() -> Dict:
    """
    Get report of matches that have ALREADY STARTED (Live or Complete).

    Returns:
        Dictionary with started matches or status message
    """
    try:
        # Ensure we have matches
        matches = load_stored_matches()

        if not matches:
            logger.warning("📅 No matches scheduled for today")
            return {"status": "No matches scheduled for today"}

        # Check real-time status
        started, upcoming = check_all_matches()

        if not started:
            logger.info(f"⏳ No matches started yet. {len(upcoming)} upcoming.")
            return (
            f"⏳ No matches have started yet. There are {len(upcoming)} matches "
            "{upcoming} scheduled for later today, currently in 'Upcoming' status."
        )

    # Case C: Success - Format the report for matches that are active or done
        logger.info(f"✅ {len(started)} matches started")
        return started



    except Exception as e:
        logger.error(f"❌ Error in match report: {e}")
        return {"status": f"Error: {str(e)}", "error": True}

def generate_match_context_key(match: str, scout_type: str) -> str:
    """
    Generates a unique key like: 'eco_match_context_nz_vs_rsa'
    or 'form_match_context_nz_vs_rsa'
    """
    clean_match = match.lower().replace(' ', '_')
    return f"{scout_type}_match_context_{clean_match}"

def get_or_generate_match_context(match_id:int,match: str, venue: str = None,city:str =None) -> dict:
    """
    REASONING SNAPSHOT STRATEGY:
    - First call: Generate context by running all tools ONCE
    - Subsequent calls: Return cached context (NO tool calls)

    Returns: {"context": full_match_context_string, "is_cached": bool}
    """
    cache_key = generate_match_context_key(match, "eco")


    # Check if context already exists in cache
    if cache.exists(cache_key):

        try:
            cached_data = cache.get(cache_key)
            print(cached_data)
            logger.info(f"✅ [SNAPSHOT] Reusing cached match context for {match}")
            return {
                "context": cached_data['context'],
                "is_cached": True,
                "cached_at": cached_data.get('timestamp', 'unknown')
            }
        except Exception as e:
            logger.warning(f"⚠️ Failed to retrieve cached context: {e}")

    # No cache: Generate fresh context by calling all tools
    logger.info(f"📸 [SNAPSHOT] Generating fresh match context for {match}")

    try:
        # Call all tools in sequence to build complete context
        # venue_data = get_match_venue(match)
        squads_data = get_cricket_squads_by_match(match_id)

        # For Eco-Scout: also get weather and pitch
        weather_data = get__weathr(city, datetime.now().strftime("%Y-%m-%d"))
        combined_location = f"venue_name {venue} + city {city}" # Placeholder city
        pitch_data = get_match_environment(location= combined_location)

        # Combine all data into one comprehensive context
        full_context = f"""
=== MATCH REASONING SNAPSHOT ===
Generated at: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S IST')}
Match: {match}


--- PLAYING SQUADS ---
{squads_data}

--- WEATHER CONDITIONS ---
{weather_data}

--- PITCH ANALYSIS ---
{pitch_data}

=== END SNAPSHOT ===
"""

        # Cache the entire context as a snapshot
        cache.set(cache_key, {"context": full_context})
        logger.info(f"✅ [SNAPSHOT] Cached complete match context ({len(full_context)} chars)")

        return {
            "context": full_context,
            "is_cached": False,
            "generated_at": datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S IST')
        }

    except Exception as e:
        logger.error(f"❌ [SNAPSHOT] Failed to generate match context: {e}")
        return {
            "context": f"Error generating context: {str(e)}",
            "is_cached": False,
            "error": str(e)
        }
# Assuming IST and cache are defined globally in your environment
# IST = pytz.timezone('Asia/Kolkata')

def get_or_generate_match_context_for_form(match_id: int, match: str) -> dict:
    """
    FORM-SCOUT SNAPSHOT STRATEGY:
    1. Check if a complete form context exists in cache.
    2. If not, invoke the dictionary-based squad tool.
    3. Extract all player IDs directly from the dictionary.
    4. Fetch batch stats for those players.
    5. Save the combined data as a single 'Snapshot' for the Form-Scout agent.
    """
    cache_key = generate_match_context_key(match, "form")

    # --- 1. CACHE CHECK ---
    if cache.exists(cache_key):
        try:
            cached_data = cache.get(cache_key)
            logger.info(f"✅ [FORM SNAPSHOT] Reusing cached context for Match ID: {match_id}")
            return {
                "context": cached_data['context'],
                "is_cached": True,
                "timestamp": cached_data.get('timestamp')
            }
        except Exception as e:
            logger.warning(f"⚠️ Failed to retrieve cached form context: {e}")

    # --- 2. GENERATE FRESH CONTEXT ---
    logger.info(f"📸 [FORM SNAPSHOT] Generating fresh Form context for {match} (ID: {match_id})")

    try:
        # Step 1: Get Squad Data (Invoking the tool that returns a JSON dict)
        # This tool returns: {"match_id": 123, "teams": {"team1": {"players": [{"id": "1", ...}] ...}}}
        squad_json = get_cricket_squads_by_match(match_id)
        squad_data = json.loads(squad_json)

        print('squad data is collected')

        if "error" in squad_data:
            raise ValueError(f"Squad API Error: {squad_data['error']}")

        # Step 2: Pick Player IDs easily from the structured dictionary
        all_player_ids = []
        for team_key in ["team1", "team2"]:
            team_info = squad_data.get("teams", {}).get(team_key, {})
            for player in team_info.get("players", []):
                if "id" in player:
                    all_player_ids.append(str(player["id"]))

        if not all_player_ids:
            return {
                "context": "Error: No player IDs found. Squad might not be announced.",
                "is_cached": False
            }

        # Step 3: Call Batch Stats with the clean list of IDs
        logger.info(f"📊 Fetching batch stats for {len(all_player_ids)} players...")
        stats_data = get_batch_player_stats.invoke({"player_ids": all_player_ids})

        # Step 4: Build the Final Snapshot String
        # This is the ONLY thing the LLM will read to make its decision.
        full_context = f"""
=== FORM-SCOUT MATCH REASONING SNAPSHOT ===
Generated at: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S IST')}
Match: {match} (ID: {match_id})

--- OFFICIAL SQUAD DATA ---
{squad_json}

--- RECENT PLAYER PERFORMANCE (T20 FORM) ---
{stats_data}

=== END SNAPSHOT ===
"""

        # --- 3. STORE AND RETURN ---
        cache.set(cache_key, {"context": full_context})
        logger.info(f"✅ [FORM SNAPSHOT] Successfully cached complete context for {match}")

        return {
            "context": full_context,
            "is_cached": False,
            "generated_at": datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S IST')
        }

    except Exception as e:
        logger.error(f"❌ [FORM SNAPSHOT] Failed to generate context: {e}")
        return {
            "context": f"Critical Error generating Form context: {str(e)}",
            "is_cached": False
        }
# ==========================================
# TOOL REGISTRY - For easy access
# ==========================================

SCOUT_TOOLS = {
    "get_weather": get__weathr,
    "get_venue": get_match_venue,
    "get_environment": get_match_environment,
    "get_squads": get_cricket_squads_by_match,
}

STATS_TOOLS = {
    "fetch_stats": fetch_match_stats,
    "calculate_points": calculate_fantasy_points_2026,
    "get_selections": get_user_selections_from_sheet,
    "calculate_leaderboard": calculate_leaderboard,
    "fetch_single_player_stat": fetch_single_player_stat,
    "get_batch_player_stats": get_batch_player_stats,
}

MATCH_TOOLS = {
    "get_todays_match_list": get_todays_match_list,
    "load_stored_matches": load_stored_matches,
    "check_match_status": check_match_status,
    "check_all_matches": check_all_matches,
    "get_started_matches_report": get_started_matches_report,
}

ALL_TOOLS = {**SCOUT_TOOLS, **STATS_TOOLS, **MATCH_TOOLS}


if __name__ == "__main__":
    # Quick test
    print("✅ Tools module loaded successfully")
    print(f"Scout tools: {list(SCOUT_TOOLS.keys())}")
    print(f"Stats tools: {list(STATS_TOOLS.keys())}")
