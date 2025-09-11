from google.adk.agents import LlmAgent
from restaurantagent.tools.maptools import find_restaurants
from restaurantagent.tools.sitespider import get_menu, get_webpage_text
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
session_service = InMemorySessionService()

def create_generic_search_agent() -> LlmAgent:
    """Creates and a configures the Generic Search agent."""
    agent = LlmAgent(
        name="generic_search",
        model="gemini-2.5-pro",
        description="A helpful agent that finds information about restaurants.",
        instruction=(
            "You are a friendly and helpful assistant that finds information about restaurants. "
            "Use the 'google_search' tool to get information about restaurants."
            "Finally, present the results to the user in a clear format."
        ),
        tools=[google_search],
        output_key="google_search_results" 
    )
    return agent

menu_gatherer = LlmAgent(
    name="menu_gatherer",
    model="gemini-2.5-pro",
    description="An agent that can find and extract menu information from a restaurant's website.",
    instruction=(
        "You are an expert at finding and extracting menu information from restaurant websites. "
        "Given a restaurant's website URL, you should first use the 'find_internal_links' find the menu present within that website"
        "Present that menu in a nicely formatted format"
        "Include the menu url in the response as well"
    ),
    tools=[get_menu],
    output_key="menu_items"
)


def create_restaurant_finder_agent() -> LlmAgent:
    """Creates and configures the Restaurant Finder agent."""
    
    # The LlmAgent class is used directly.
    # We pass the configuration to its constructor.
    agent = LlmAgent(
        name="restaurant_finder",
        model="gemini-2.5-pro",
        description="A helpful agent that finds restaurants in a specified location.",
        instruction=(
            "You are a friendly and helpful assistant that finds restaurants for a user. "
            "You should first identify the location of the restaurant and then the radius and use it to find restaurants."
            "Use the 'find_restaurants' tool to get the list of restaurants. It takes the location: geographical location and radius: distance around central point, default is 1"
            "The results should include name,location, ratings, review summary of the restaurants"
            "Finally, present the results to the user in a clear format."
        ),
        # Tools are provided in a list. The ADK inspects the function signature.
        tools=[find_restaurants],
        output_key="restaurant_search_results" 
    )
    return agent