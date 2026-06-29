import json
import logging
import os
import asyncio
from functools import partial
from typing import Type, TypeVar, Any
from pydantic import BaseModel
from groq import AsyncGroq
from google import genai
from google.genai import types

from dotenv import load_dotenv
load_dotenv()

from app.core.config import settings

logger = logging.getLogger("vendormind.llm")
T = TypeVar("T", bound=BaseModel)

# Configure modern google-genai clients
genai_client = None
if settings.GEMINI_API_KEY:
    try:
        genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)
    except Exception as e:
        logger.error(f"Failed to initialize google-genai Developer client: {e}")

vertex_client = None
vertex_project = os.getenv("VERTEX_PROJECT_ID")
if vertex_project:
    try:
        vertex_client = genai.Client(
            vertexai=True,
            project=vertex_project,
            location=os.getenv("VERTEX_LOCATION", "us-central1")
        )
    except Exception as e:
        logger.error(f"Failed to initialize google-genai Vertex client: {e}")

# Configure Groq client if key is available
groq_client = None
if settings.GROQ_API_KEY:
    groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
else:
    logger.warning("GROQ_API_KEY is not set. LLM calls will fail or fall back.")

# Get preferred provider from environment
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash") # Default to gemini-1.5-flash for compatibility

async def generate_structured_data(prompt: str, response_schema: Type[T]) -> T:
    """
    Generates JSON text complying with a specific Pydantic schema.
    Returns the parsed Pydantic schema instance.
    Supports Vertex AI, Gemini Developer API, and Groq, defaulting based on LLM_PROVIDER.
    """
    # 1. Vertex AI
    if LLM_PROVIDER == "vertex" and vertex_client is not None:
        try:
            model_name = os.getenv("VERTEX_MODEL", "gemini-1.5-flash")
            loop = asyncio.get_running_loop()
            
            # Execute GenAI call in thread pool to prevent blocking the event loop
            response = await loop.run_in_executor(
                None,
                partial(
                    vertex_client.models.generate_content,
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=response_schema,
                        temperature=0.1
                    )
                )
            )
            raw_text = response.text.strip()
            data = json.loads(raw_text)
            return response_schema(**data)
        except Exception as e:
            logger.error(f"Vertex AI structured call failed: {e}")
            raise e

    # 2. Gemini Developer API (Google AI Studio)
    if LLM_PROVIDER == "gemini" and genai_client is not None:
        try:
            loop = asyncio.get_running_loop()
            
            # Execute GenAI call in thread pool to prevent blocking the event loop
            response = await loop.run_in_executor(
                None,
                partial(
                    genai_client.models.generate_content,
                    model=GEMINI_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=response_schema,
                        temperature=0.1
                    )
                )
            )
            raw_text = response.text.strip()
            data = json.loads(raw_text)
            return response_schema(**data)
        except Exception as e:
            logger.error(f"Gemini API structured call failed: {e}")
            raise e

    # 3. Fallback to Groq
    if not settings.GROQ_API_KEY or groq_client is None:
        raise ValueError("No valid LLM provider (Vertex, Gemini, or Groq) is configured or selected.")

    try:
        # Convert the Pydantic model schema to JSON schema string
        schema_json = json.dumps(response_schema.model_json_schema(), indent=2)
        
        # System instructions asking model to conform to the schema
        system_prompt = (
            "You are a strict data extraction assistant. "
            "Your task is to parse input text and return a JSON object that strictly complies with the following JSON schema:\n\n"
            f"{schema_json}\n\n"
            "Do not include any explanation, code blocks, formatting, or text outside the JSON. "
            "Return ONLY the raw JSON object."
        )

        model_name = "llama-3.3-70b-versatile"
        
        response = await groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            model=model_name,
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        raw_text = response.choices[0].message.content.strip()
        data = json.loads(raw_text)
        return response_schema(**data)
        
    except Exception as e:
        logger.error(f"Groq API structured call failed: {e}")
        raise e
