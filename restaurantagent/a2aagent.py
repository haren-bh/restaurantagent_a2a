
import logging
from google.adk.agents import LlmAgent
logging.getLogger().setLevel(logging.DEBUG)


# A2A
from a2a.types import (
    AgentSkill,
)

# ADK
from google.adk.tools import google_search_tool

# Agent Engine
from vertexai.preview.reasoning_engines.templates.a2a import create_agent_card

root_agent=LlmAgent(
    # The LLM model to use
    model="gemini-2.5-flash",
    # Internal name for the agent (used in logging and sessions)
    name="qa_assistant",
    # Human-readable description
    description="I answer questions using web search.",
    # The system instruction that guides the agent's behavior
    # This is crucial for getting good results
    instruction="""You are a helpful Q&A assistant.
        When asked a question:
        1. Use Google Search to find current, accurate information
        2. Synthesize the search results into a clear answer
        3. Cite your sources when possible
        4. If you can't find a good answer, say so honestly

        Always aim for accuracy over speculation.""",
    # Tools available to the agent
    # The agent will automatically use these when needed
    tools=[google_search_tool.google_search],
)


restaurant_finder_agent_skill=AgentSkill(

    # Unique identifier for this skill
    id="restaurant_finder",
    # Human-friendly name
    name="Restaurant Finder",
    # Detailed description helps clients understand when to use this skill
    description="Finds the restaurants near a location",
    # Tags for categorization and discovery
    # These help in agent marketplaces or registries
    tags=["restaurant finding", "restaurant search", "restaurant finder"],
    # Examples show clients what kinds of requests work well
    # This is especially helpful for LLM-based clients
    examples=[
        "Find me good restaurants near Shibuya station within 3Kms",
        "Find me good restaurants near Tokyo station within 5Kms",
    ],
    # Optional: specify input/output modes
    # Default is text, but could include images, files, etc.
    input_modes=["text/plain"],
    output_modes=["text/plain"],
)

restaurant_finder_agent_card = create_agent_card(
    agent_name="Restaurant Finder",
    description="Finds the restaurants near a location",
    skills=[restaurant_finder_agent_skill],
)
