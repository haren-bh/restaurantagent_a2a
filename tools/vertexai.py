import os
from google import genai
from google.genai import types
from typing import Optional
import logging
from ..settings import *


# Get a logger for this module
logger = logging.getLogger(__name__)

def call_gemini(
    prompt: str, 
    url: Optional[str] = None, 
    mimetype: Optional[str] = None, 
    project: Optional[str] = None, 
    location: Optional[str] = None
) -> str:
    """
    Generates content from a prompt and an optional image, returning the result as a string.
    It retrieves project and location from function arguments or OS environment variables.

    Args:
        prompt (str): The text prompt to send to the model.
        url (str, optional): The URI of the image file. Defaults to None.
        mimetype (str, optional): The MIME type of the image. Required if URL is provided.
                                  Defaults to None.
        project (str, optional): The Google Cloud project ID. Defaults to env var.
        location (str, optional): The location for the Vertex AI client. Defaults to env var.

    Returns:
        str: The generated text response from the model.
        
    Raises:
        ValueError: If project/location is not set, or if URL is given without a MIME type.
    """
    try:
        logger.info(f"Calling Gemini with prompt: '{prompt}' and URL: '{url}'")
        project_id = project or os.environ.get("GOOGLE_CLOUD_PROJECT") or GOOGLE_CLOUD_PROJECT
        location_name = location or os.environ.get("GOOGLE_CLOUD_LOCATION") or GOOGLE_CLOUD_LOCATION


        if not project_id or not location_name:
            raise ValueError(
                "You must provide 'project' and 'location' as arguments or set "
                "the GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION environment variables."
            )

        client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location_name,
        )

        # Start building the list of parts with the mandatory text prompt
        request_parts = [types.Part.from_text(text=prompt)]

        # If a URL is provided, validate and add the image part
        if url:
            if not mimetype:
                raise ValueError("MIME type must be provided if a URL is given.")
            image_part = types.Part.from_uri(file_uri=url, mime_type=mimetype)
            request_parts.append(image_part)

        model = "gemini-2.5-flash-lite"
        
        contents = [
            types.Content(
                role="user",
                parts=request_parts
            )
        ]

        generate_content_config = types.GenerateContentConfig(
            temperature=1,
            top_p=0.95,
            max_output_tokens=65535,
            safety_settings=[
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF")
            ],
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        )
        
        response_chunks = []
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            response_chunks.append(chunk.text)
            
        full_response = "".join(response_chunks)
        logger.info(f"Gemini call successful. Returning response (len={len(full_response)}).")
        return full_response

    except Exception as e:
        logger.error(f"An error occurred in call_gemini: {e}", exc_info=True)
        return ""


#print(call_gemini("what is this","https://gonpachi.jp/wp-content/uploads/sites/18/2020/01/gonpachi-shibuya-atmosphere5.jpg","image/jpeg"))