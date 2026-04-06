from typing import Union
from langchain_core.tools import tool
# Import the factories from your agent files
from agents.form_agent import create_form_scout_with_snapshot
from agents.eco_agent import create_eco_scout_with_snapshot

@tool
def call_form_scout(match_details: Union[str, dict]) -> str:
    """Delegates to the Form-Scout Expert using snapshot-based context."""
    try:
        # 1. Create the agent for this specific match
        form_agent = create_form_scout_with_snapshot(match_details, 'form')

        # 2. Ask the agent to do its job
        response = form_agent.invoke({"input": f"Pick the Form-Scout 11 for: {match_details}"})

        # 3. Handle the structured response
        if hasattr(response, 'model_dump_json'):
             return response.model_dump_json()
        return str(response)
    except Exception as e:
        return f"Error in Form-Scout: {str(e)}"

@tool
def call_eco_scout(match_details: Union[str, dict]) -> str:
    """Delegates to the Eco-Scout Expert using snapshot-based context."""
    try:
        eco_agent = create_eco_scout_with_snapshot(match_details, 'eco')
        response = eco_agent.invoke({"input": f"Pick the Eco-Scout 11 for: {match_details}"})

        if hasattr(response, 'model_dump_json'):
             return response.model_dump_json()
        return str(response)
    except Exception as e:
        return f"Error in Eco-Scout: {str(e)}"