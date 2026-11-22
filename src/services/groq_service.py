
import json
import os
import re

from dotenv import load_dotenv
from groq import Groq

from src.services.extraction_schema import ExtractionResult

# ==========================================
# STEP 1: LOAD API KEY
# ==========================================

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    raise ValueError("GROQ_API_KEY is missing from .env")

client = Groq(api_key=API_KEY)

MODEL_NAME = "openai/gpt-oss-120b"


# ==========================================
# STEP 2: NORMALIZE ENTITY TYPES
# ==========================================

def normalize_entity_types(data):

    entities = data.get("entities", [])

    for entity in entities:

        entity_type = str(
            entity.get("entity_type") or ""
        ).strip().lower()

        if entity_type in [
            "product",
            "ai product",
            "ai-product",
            "ai_product"
        ]:
            entity["entity_type"] = "ai_product"

        elif entity_type in [
            "company",
            "startup",
            "ai startup"
        ]:
            entity["entity_type"] = "startup"

    return data


# ==========================================
# STEP 3: CLEAN JSON RESPONSE
# ==========================================

def clean_json_response(response_text):

    if not response_text:
        raise ValueError("Groq returned an empty response")

    response_text = response_text.strip()

    # Remove Markdown code fences if present
    response_text = re.sub(
        r"^```(?:json)?\s*",
        "",
        response_text,
        flags=re.IGNORECASE
    )

    response_text = re.sub(
        r"\s*```$",
        "",
        response_text
    )

    return response_text.strip()


# ==========================================
# STEP 4: EXTRACT AI ENTITIES
# ==========================================

def extract_entities(source_text):

    if not source_text or not source_text.strip():
        raise ValueError("Source text cannot be empty")

    prompt = f"""
You are an AI data extraction assistant.

Extract AI startups and AI products from the
source text provided below.

IMPORTANT RULES:

1. Extract only information supported by the text.
2. Never invent company names or website URLs.
3. Use null when information is unavailable.
4. Distinguish startups from AI products.
5. Every entity_type MUST be exactly one of:
   "startup" or "ai_product".
6. Do not use "product", "company", or other
   alternative entity_type values.
7. Return valid JSON only.
8. Follow the exact JSON structure below.

EXPECTED JSON:

{{
    "entities": [
        {{
            "entity_type": "startup",
            "name": "Company name",
            "website_url": null,
            "description": null,
            "category": null,
            "developer": null,
            "pricing_model": null,
            "launch_date": null
        }},
        {{
            "entity_type": "ai_product",
            "name": "Product name",
            "website_url": null,
            "description": null,
            "category": null,
            "developer": null,
            "pricing_model": null,
            "launch_date": null
        }}
    ]
}}

SOURCE TEXT:

{source_text}
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    response_text = response.choices[0].message.content

    # Clean response
    response_text = clean_json_response(response_text)

    # Convert JSON text into Python dictionary
    data = json.loads(response_text)

    # Normalize entity types
    data = normalize_entity_types(data)

    # Validate using Pydantic schema
    result = ExtractionResult.model_validate(data)

    return result


# ==========================================
# STEP 5: TEST GROQ SERVICE
# ==========================================

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

        print("\nGROQ STRUCTURED EXTRACTION")
        print("=" * 50)

        print(result.model_dump_json(indent=2))

        print("\nEXTRACTION SUMMARY")
        print("=" * 50)

        print("Total entities:", len(result.entities))

        for entity in result.entities:
            print(
                entity.entity_type,
                "|",
                entity.name
            )

        print("\nGROQ EXTRACTION SUCCESSFUL")

    except Exception as error:  # noqa: BLE001

        print("\nGROQ EXTRACTION FAILED")
        print("=" * 50)

        print(type(error).__name__, ":", error)
