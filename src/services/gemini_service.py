
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.services.extraction_schema import ExtractionResult

# Load environment variables
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY is missing from .env")


# Initialize Gemini
client = genai.Client(api_key=API_KEY)

MODEL_NAME = "gemini-3.1-flash-lite"


def extract_entities(source_text):

    prompt = f"""
    Extract AI startups and AI products from the
    source text provided below.

    Rules:
    1. Extract only information supported by the text.
    2. Do not invent company names or website URLs.
    3. Use null when information is unavailable.
    4. Distinguish startups from AI products.
    5. Return all relevant entities found.

    SOURCE TEXT:
    {source_text}
    """

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ExtractionResult
        )
    )

    if response.parsed is not None:
        result = ExtractionResult.model_validate(response.parsed)
    else:
        result = ExtractionResult.model_validate_json(response.text) # type: ignore

    return result


if __name__ == "__main__":

    sample_text = """
    TechNova AI is an artificial intelligence startup.

    The company develops SmartWriter, an AI writing
    assistant that helps users create articles and
    business documents.

    Its official website is https://example.com.
    The article does not mention its pricing or launch date.
    """

    try:
        result = extract_entities(sample_text)

        print("\nSTRUCTURED GEMINI EXTRACTION")
        print("=" * 40)

        print(result.model_dump_json(indent=2))

    except Exception as error:  # noqa: BLE001
        print("Extraction failed:", error)
