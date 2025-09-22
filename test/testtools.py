# Helpers
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


def receive_wrapper(data: dict) -> Callable[[], Awaitable[dict]]:
    """Creates a mock ASGI receive callable for testing."""

    async def receive():
        byte_data = json.dumps(data).encode("utf-8")
        return {"type": "http.request", "body": byte_data, "more_body": False}

    return receive


def build_post_request(
    data: dict[str, Any] | None = None, path_params: dict[str, str] | None = None
) -> Request:
    """Builds a mock Starlette Request object for a POST request with JSON data."""
    scope = {
        "type": "http",
        "http_version": "1.1",
        "headers": [(b"content-type", b"application/json")],
        "app": None,
    }
    if path_params:
        scope["path_params"] = path_params
    receiver = receive_wrapper(data)
    return Request(scope, receiver)


def build_get_request(path_params: dict[str, str]) -> Request:
    """Builds a mock Starlette Request object for a GET request."""
    scope = {
        "type": "http",
        "http_version": "1.1",
        "query_string": b"",
        "app": None,
    }
    if path_params:
        scope["path_params"] = path_params

    async def receive():
        return {"type": "http.disconnect"}

    return Request(scope, receive)


def get_bearer_token() -> str | None:
    """Fetches a Google Cloud bearer token using Application Default Credentials."""
    try:
        # Use an alias to avoid name collision with starlette.requests.Request
        credentials, project = default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        request = req()
        credentials.refresh(request)
        return credentials.token
    except Exception as e:
        print(f"Error getting credentials: {e}")
        print(
            "Please ensure you have authenticated with 'gcloud auth application-default login'."
        )
    return None