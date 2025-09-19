
import logging
from google.adk.agents import LlmAgent
import json
import logging
import time
from collections.abc import Awaitable, Callable
from datetime import datetime
from pprint import pprint
from typing import Any, NoReturn

import httpx
from google.auth import default
from google.auth.transport.requests import Request as req
from starlette.requests import Request
logging.getLogger().setLevel(logging.INFO)


# A2A
from a2a.client import ClientConfig, ClientFactory
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    AgentSkill,
    Message,
    Part,
    Role,
    TaskState,
    TaskQueryParams,
    TextPart,
    TransportProtocol,
    UnsupportedOperationError,
)
from a2a.utils import new_agent_text_message
from a2a.utils.errors import ServerError

# ADK
from google.adk import Runner
from google.adk.agents import LlmAgent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search_tool
from google.genai import types

# Agent Engine
from vertexai.preview.reasoning_engines import A2aAgent
from vertexai.preview.reasoning_engines.templates.a2a import create_agent_card

from restaurantagent.agents.agents import create_restaurant_finder_agent,menu_gatherer,create_generic_search_agent
from google.adk.sessions import InMemorySessionService, Session
temp_service = InMemorySessionService()

# Configure logging to show detailed output from all modules
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

restaurant_finder_agent = create_restaurant_finder_agent()
generic_search_agent=create_generic_search_agent()

def create_root_agent() -> LlmAgent:
    """Creates and configures the Root agent."""

    # A delegating LlmAgent uses its own LLM to route user requests to the
    # appropriate sub-agent based on their descriptions.
    agent = LlmAgent(
        name="root_agent",
        model="gemini-2.5-pro",
        description="Top level agent that acts as controller",
        instruction=(
            "You are a master controller agent that delegates tasks to specialized sub-agents. "
            "Analyze the user's request and route it to the correct agent based on the following rules:\n"
            "1. For finding restaurants: If the user asks to find restaurants, eateries, or food places "
            "(e.g., 'find me some restaurants', 'any good pizza places nearby?'), you MUST use the `restaurant_agent`.\n"
            "2. For finding menus: If the user asks for the menu of a specific restaurant, you MUST use the `restaurant_menu_agent`. If the user asks menu for all the restaurants, find the menu of all the restaurants one at a time and show the menu\n"
            "3. For general questions: For any other topic, question, or request that is not about finding restaurants or their menus, "
            "you MUST use the `generic_search_agent`.\n"
            "4. For combined requests: If the user asks to find restaurants AND their menus, first use `restaurant_agent` to find the list of restaurants, "
            "and then use `restaurant_menu_agent` to get the menus for the results."
        
            ),
        #sub_agents=[restaurant_finder_agent,menu_gatherer,generic_search_agent],
        #sub_agents=[restaurant_finder_agent,menu_gatherer],
        output_key="searched_restaurant_info"
    )
    return agent

#root_agent=create_root_agent()

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
