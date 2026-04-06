from typing import List
from pydantic import BaseModel, Field
from langchain.agents.structured_output import ToolStrategy
from typing import List, Optional
from pydantic import BaseModel, Field

class FantasyPlayer(BaseModel):
    """Information about a single selected fantasy player."""
    player_id: str = Field(description="The unique ID of the player from the squad tool")
    name: str = Field(description="Full name of the player")
    team: str = Field(description="Team name of the player")
    role: str = Field(description="Role: BAT, BOWL, AR, or WK")
    scout_logic: str = Field(description="Detailed reasoning for selecting this player")

# 2. CREATE THIS NEW CONTAINER CLASS
class FantasyTeam(BaseModel):
    """The full squad of 11 players."""
    reasoning_summary: str = Field(description="Overall logic for the whole team")
    players: List[FantasyPlayer] = Field(description="A list of exactly 11 selected players")



