# Restaurant Agent

This project is a multi-agent application built with the Google Agent Development Kit (ADK). It is designed to help users find restaurants, retrieve their menus, and get general information about them.

## Features

- **Find Restaurants**: Locates restaurants near a specified address or landmark using the Google Maps API.
- **Gather Menus**: Scrapes restaurant websites to find and extract menu information from web pages, PDFs, and even images using Gemini Vision.
- **General Search**: Performs general web searches for any other restaurant-related queries.

## Architecture

The application uses a hierarchical agent structure to delegate tasks effectively:

- **`root_agent`**: The main controller agent. It analyzes the user's request and routes it to the appropriate sub-agent.
- **`restaurant_finder_agent`**: A specialized agent that uses the `find_restaurants` tool to search for restaurants via the Google Maps API.
- **`menu_gatherer`**: A sub-agent responsible for extracting menu information from a restaurant's website using the `get_menu` tool, which leverages web scraping and Gemini Vision.
- **`generic_search_agent`**: A sub-agent that handles general queries by using the `google_search` tool.

## Prerequisites

- Python 3.11+
- Poetry for dependency management.
- Google Cloud SDK installed and authenticated.

## Setup and Installation

1.  **Clone the repository:**
    ```sh
    git clone <your-repository-url>
    cd restaurantagent
    ```

2.  **Install dependencies:**
    Use Poetry to install the dependencies defined in `pyproject.toml`.
    ```sh
    poetry install
    ```

3.  **Configure Environment Variables:**
    The agent requires API keys and Google Cloud configuration.

    - Copy the example environment file:
      ```sh
      cp .env.example .env
      ```

    - Open the `.env` file and add your specific credentials.

4.  **Authenticate with Google Cloud:**
    This agent uses Application Default Credentials (ADC) to interact with Vertex AI.
    ```sh
    gcloud auth application-default login
    ```

## Configuration

The `.env` file requires the following variables:

- `GOOGLE_CLOUD_PROJECT`: Your Google Cloud Project ID. Used by the `call_gemini` tool for Vertex AI.
- `GOOGLE_CLOUD_LOCATION`: The Google Cloud region for your project (e.g., `us-central1`). Used by the `call_gemini` tool.
- `GOOGLE_MAPS_API_KEY`: Your Google Maps API key with the "Places API" enabled. Used by the `find_restaurants` tool.

## Usage

### Running Locally

You can run the agent locally for development and testing using the ADK CLI. This will start a local web server.

```sh
poetry run adk run restaurantagent
```

You can then interact with the agent by sending requests to `http://127.0.0.1:8000/`.

### Deploying to Agent Engine

To deploy the agent to Google Cloud's Agent Engine, you first need to ensure the necessary APIs are enabled:

```sh
gcloud services enable aiplatform.googleapis.com
gcloud services enable agentengine.googleapis.com
```

Then, run the `adk deploy` command. The `--env-file` flag securely passes your local `.env` file's contents as environment variables to the deployed service.

```sh
poetry run adk deploy restaurantagent --project <your-gcp-project-id> --location <your-gcp-location> --env-file .env
```

After a few minutes, the command will output the URL of your deployed agent endpoint.