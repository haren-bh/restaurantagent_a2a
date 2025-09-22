import vertexai
from google.genai import types
from restaurantagent.agentexecutor import RestaurantFinderExecutor
from restaurantagent.agent import restaurant_finder_agent_card

# Agent Engine
from vertexai.preview.reasoning_engines import A2aAgent



# !gsutil mb -l $LOCATION -p $PROJECT_ID $BUCKET_URI
from vertexai import agent_engines
PROJECT_ID = "datapipeline-372305" #TODO change this 変更してください
LOCATION = "us-central1"
STAGING_BUCKET = "gs://haren-genai-data" #TODO change this　変更してください, 例: gs://bucket-name
BUCKET_URI=STAGING_BUCKET
# Initialize Vertex AI session
vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=BUCKET_URI)

# Initialize the Gen AI client using http_options
# The parameter customizes how the Vertex AI client communicates with Google Cloud's backend services.
# It's used here to access new, pre-release features.

client = vertexai.Client(
    project=PROJECT_ID,
    location=LOCATION,
    http_options=types.HttpOptions(
        api_version="v1beta1", base_url=f"https://{LOCATION}-aiplatform.googleapis.com/"
    ),
)

a2a_agent = A2aAgent(agent_card=restaurant_finder_agent_card, agent_executor_builder=RestaurantFinderExecutor)
a2a_agent.set_up()


vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=STAGING_BUCKET,
)

remote_a2a_agent = client.agent_engines.create(
    # The actual agent to deploy
    agent=a2a_agent,
    config={
        # Display name shown in the console
        "display_name": a2a_agent.agent_card.name,
        # Description for documentation
        "description": a2a_agent.agent_card.description,
        # Python dependencies needed in Agent Engine
        "requirements": [
            "google-cloud-aiplatform[agent_engines,adk]>=1.112.0",
            "a2a-sdk >= 0.3.4",
            "beautifulsoup4>=4.13.4",
            "googlemaps",
            "google-genai",
            "python-dotenv",
            "./dist/restaurantagent-0.1.0-py3-none-any.whl",
        ],
        "extra_packages":[
        "./dist/restaurantagent-0.1.0-py3-none-any.whl", #TODO 確認
        ],
        # Http options
        "http_options": {
            "base_url": f"https://{LOCATION}-aiplatform.googleapis.com",
            "api_version": "v1beta1",
        },
        # Staging bucket
        "staging_bucket": BUCKET_URI,
    },
)


