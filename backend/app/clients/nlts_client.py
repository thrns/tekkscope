import json
import logging
import os
from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from app.research import run_research
from app.research_lib.api.settings_utils import create_settings_snapshot
from app.research_lib.config.llm_config import get_llm as get_configured_llm
from app.research_lib.config.provider_router import provider_overrides_from_env

logger = logging.getLogger(__name__)


def get_llm():
    max_tokens = int(
        os.getenv("LDR_LLM_MAX_TOKENS", os.getenv("TEKK_LLM_MAX_TOKENS", "8000"))
    )
    overrides = provider_overrides_from_env(
        max_tokens=max_tokens,
        temperature=0,
        search_tool="searxng",
        search_instance_url=os.getenv(
            "TEKK_SEARXNG_URL", "https://search.tekkscope.com"
        ),
    )
    settings_snapshot = create_settings_snapshot(overrides=overrides)
    return get_configured_llm(settings_snapshot=settings_snapshot)

# Define the state for the graph
class NLTSState(TypedDict):
    query: str
    schema: Optional[Dict[str, Any]]
    research_results: Optional[str]
    structured_output: Optional[Any]
    error: Optional[str]

# --- Nodes ---

def infer_schema_node(state: NLTSState) -> NLTSState:
    """Infers a JSON schema from the query if not provided."""
    if state.get("schema"):
        return state

    query = state["query"]
    logger.info(f"Inferring schema for query: {query}")

    try:
        llm = get_llm()

        prompt = f"""You are a data schema expert.
Generate a valid JSON Schema (draft-07) that best fits the following user query.
The schema should describe the structure of the data the user is looking for.
Return ONLY the JSON Schema object. Do not include markdown formatting or explanations.

User Query: "{query}"
"""
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content.strip()
        
        # Clean up markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        schema = json.loads(content)
        return {**state, "schema": schema}
    except Exception as e:
        logger.error(f"Error inferring schema: {e}")
        return {**state, "error": f"Failed to infer schema: {e}"}


def conduct_research_node(state: NLTSState) -> NLTSState:
    """Conducts research using the research_lib."""
    if state.get("error"):
        return state

    query = state["query"]
    logger.info(f"Conducting research for query: {query}")

    try:
        # Use quick_summary for faster results, or configurable
        # We use the run_research wrapper from app.research
        results = run_research(query, mode="quick")
        
        # Format results into a string for the LLM
        research_text = ""
        if isinstance(results, dict):
            research_text += f"Summary: {results.get('summary', '')}\n\n"
            research_text += "Key Findings:\n"
            for item in results.get("key_findings", []):
                research_text += f"- {item}\n"
            
            # Add some content from sources if available (simplified)
            # In a real implementation, we might want to pass more raw data
        else:
            research_text = str(results)

        return {**state, "research_results": research_text}
    except Exception as e:
        logger.error(f"Error conducting research: {e}")
        return {**state, "error": f"Failed to conduct research: {e}"}


def extract_data_node(state: NLTSState) -> NLTSState:
    """Extracts structured data from research results based on the schema."""
    if state.get("error"):
        return state

    schema = state["schema"]
    research_results = state["research_results"]
    query = state["query"]
    
    logger.info("Extracting structured data...")

    try:
        llm = get_llm()

        schema_str = json.dumps(schema, indent=2)
        
        prompt = f"""You are a precise data extraction AI.
Extract information from the provided Research Results to populate a JSON object that strictly follows the given JSON Schema.
If information is missing for a field, use null.

User Query: "{query}"

JSON Schema:
{schema_str}

Research Results:
{research_results}

Return ONLY the valid JSON object matching the schema. Do not include markdown formatting.
"""
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content.strip()

        # Clean up markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        structured_output = json.loads(content)
        return {**state, "structured_output": structured_output}
    except Exception as e:
        logger.error(f"Error extracting data: {e}")
        return {**state, "error": f"Failed to extract data: {e}"}


# --- Graph Construction ---

def create_nlts_graph():
    workflow = StateGraph(NLTSState)

    workflow.add_node("infer_schema", infer_schema_node)
    workflow.add_node("conduct_research", conduct_research_node)
    workflow.add_node("extract_data", extract_data_node)

    # Conditional entry point
    def check_schema(state: NLTSState):
        if state.get("schema"):
            return "conduct_research"
        return "infer_schema"

    workflow.set_conditional_entry_point(
        check_schema,
        {
            "infer_schema": "infer_schema",
            "conduct_research": "conduct_research"
        }
    )

    workflow.add_edge("infer_schema", "conduct_research")
    workflow.add_edge("conduct_research", "extract_data")
    workflow.add_edge("extract_data", END)

    return workflow.compile()

# Global instance
nlts_app = create_nlts_graph()

async def process_nlts_request(query: str, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Process a Natural Language to Structured request.
    """
    initial_state = {
        "query": query,
        "schema": schema,
        "research_results": None,
        "structured_output": None,
        "error": None
    }

    # Run the graph
    # Note: langgraph invoke is sync by default, but we can use ainvoke if needed.
    # For now, running synchronously in the thread pool via fastapi is fine, 
    # or we can use ainvoke if we want async.
    
    # Using invoke for simplicity as the nodes are sync (except run_research might block)
    # Ideally run_research should be async or we run this in a thread.
    # Since run_research in app.research is sync (calls ldr_api.quick_summary which is sync wrapper),
    # we can run this whole thing in a thread pool or just use invoke.
    
    result = await nlts_app.ainvoke(initial_state)
    
    if result.get("error"):
        raise Exception(result["error"])
        
    return {
        "structured_output": result["structured_output"],
        "schema_used": result["schema"],
        "research_summary": result["research_results"][:500] + "..." if result["research_results"] else None
    }
