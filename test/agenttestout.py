import asyncio
from restaurantagent.agentexecutor import RestaurantFinderExecutor
from restaurantagent.agent import restaurant_finder_agent_card
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
# Agent Engine
from vertexai.preview.reasoning_engines import A2aAgent
from vertexai.preview.reasoning_engines.templates.a2a import create_agent_card
from test.testtools import build_get_request,build_post_request
import pprint
import logging
import os
import time
import os
import asyncio
import logging
import pprint



async def run_full_task():
    """
    This single async function handles the entire workflow:
    1. Sets up the agent.
    2. Sends the initial message.
    3. Polls for the result until completion.
    """
    # 1. Set up the agent
    # You can do this outside the async function if the agent object
    # doesn't require an active event loop for its __init__
    a2a_agent = A2aAgent(agent_card=restaurant_finder_agent_card, agent_executor_builder=RestaurantFinderExecutor)
    a2a_agent.set_up()

    # 2. Send the initial message
    print("--- Sending Message ---")
    message_data = {
        "message": {
            "messageId": f"msg-{os.urandom(8).hex()}",
            "content": [{"text": "Find restaurants within 5Km of shibuya station"}],
            "role": "ROLE_USER",
        },
    }
    request = build_post_request(message_data)
    initial_response = await a2a_agent.on_message_send(request=request, context=None)
    
    print("Initial response:")
    pprint.pprint(initial_response)
    
    # Safely get the task ID
    try:
        task_id = initial_response["task"]["id"]
        print(f"\n--- Polling for Task ID: {task_id} ---")
    except (KeyError, TypeError):
        print("Error: Could not retrieve task ID from the initial response.")
        return

    # 3. Poll for the result in a loop
    task_data = {"id": task_id}
    request = build_get_request(task_data)
    
    while True:
        response = await a2a_agent.on_get_task(request=request, context=None)
        status = response.get("status", {}).get("state", "UNKNOWN")
        logging.info(f"Current task state: {status}")

        if status == "TASK_STATE_COMPLETED":
            print("\n--- Task Completed Successfully ---")
            pprint.pprint(response)
            break
        elif status in ["TASK_STATE_FAILED", "TASK_STATE_CANCELLED"]:
            print(f"\n--- Task ended with state: {status} ---")
            pprint.pprint(response)
            break

        # Wait for 5 seconds before polling again.
        # This yields control to the event loop, allowing background tasks to run.
        await asyncio.sleep(5)


if __name__ == "__main__":
    # Use a single asyncio.run() to execute the entire asynchronous workflow
    try:
        asyncio.run(run_full_task())
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")