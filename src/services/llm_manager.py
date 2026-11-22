
import logging
import os
import random
import re
import threading
import time

from datetime import datetime, timezone

from dotenv import load_dotenv
from openai import OpenAI

from src.services.gemini_service import (
    extract_entities as gemini_extract_entities,
)

from src.services.groq_service import (
    extract_entities as groq_extract_entities,
)

from src.services.extraction_schema import ExtractionResult


# ==================================================
# 1. CONFIGURATION
# ==================================================

load_dotenv()

MAX_RETRIES = 3
MAX_CONCURRENT_REQUESTS = 2

CHUNK_SIZE = 8000
CHUNK_OVERLAP = 500
MAX_CHUNK_DEPTH = 5

API_SEMAPHORE = threading.BoundedSemaphore(
    MAX_CONCURRENT_REQUESTS
)


# ==================================================
# 2. LOGGING
# ==================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ==================================================
# 3. DEEPSEEK CONFIGURATION
# ==================================================

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

deepseek_client = None

if DEEPSEEK_API_KEY:

    deepseek_client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com",
        max_retries=0,
        timeout=60.0,
    )

    logger.info("DeepSeek provider configured")

else:
    logger.info(
        "DeepSeek skipped: API key not configured"
    )


def deepseek_extract_entities(source_text):
    """Extract structured entities using DeepSeek."""

    if deepseek_client is None:
        raise RuntimeError(
            "DeepSeek API key is not configured"
        )

    prompt = f"""
Extract AI startups and AI products from the
following source text.

Rules:
- Extract only entities supported by the text.
- Do not invent names or URLs.
- Use null for unavailable information.
- Distinguish startups from AI products.
- Return valid JSON matching this structure:

{{
    "entities": [
        {{
            "entity_type": "startup or ai_product",
            "name": "string or null",
            "website_url": "string or null",
            "description": "string or null",
            "category": "string or null",
            "developer": "string or null",
            "pricing_model": "string or null",
            "launch_date": "string or null"
        }}
    ]
}}

SOURCE TEXT:
{source_text}
"""

    response = deepseek_client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError(
            "DeepSeek returned an empty response"
        )

    return ExtractionResult.model_validate_json(content)


# ==================================================
# 4. PROVIDER CONFIGURATION
# ==================================================

PROVIDERS = [
    {
        "name": "Gemini",
        "function": gemini_extract_entities,
    },
    {
        "name": "Groq",
        "function": groq_extract_entities,
    },
]

if deepseek_client is not None:

    PROVIDERS.append(
        {
            "name": "DeepSeek",
            "function": deepseek_extract_entities,
        }
    )


# ==================================================
# 5. HTTP STATUS DETECTION
# ==================================================

def get_http_status(error):
    """Identify HTTP status codes from provider errors."""

    status = getattr(error, "status_code", None)

    if status is None:
        status = getattr(error, "code", None)

    if status is None:

        response = getattr(
            error,
            "response",
            None,
        )

        if response is not None:
            status = getattr(
                response,
                "status_code",
                None,
            )

    try:
        if status is not None:
            return int(status)
    except (ValueError, TypeError):
        pass

    match = re.search(
        r"\b(413|429|500|502|503|504)\b",
        str(error),
    )

    if match:
        return int(match.group(1))

    return None


# ==================================================
# 6. SEMANTIC TEXT CHUNKING
# ==================================================

def split_text_semantically(
    text,
    max_chars=CHUNK_SIZE,
    overlap_chars=CHUNK_OVERLAP,
):
    """
    Split text into manageable overlapping chunks.

    Every returned chunk stays within max_chars.
    """

    if not text or not text.strip():
        return []

    if max_chars <= 0:
        raise ValueError(
            "max_chars must be greater than zero"
        )

    # Avoid excessive overlap for small test chunks.
    overlap_chars = max(
        0,
        min(overlap_chars, max_chars // 5),
    )

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:

        remaining = text_length - start

        if remaining <= max_chars:

            final_chunk = text[start:].strip()

            if final_chunk:
                chunks.append(final_chunk)

            break

        end = start + max_chars

        # Prefer paragraph, sentence, or word boundaries.
        search_area = text[start:end]

        boundary_candidates = [
            search_area.rfind("\n"),
            search_area.rfind(". "),
            search_area.rfind("? "),
            search_area.rfind("! "),
            search_area.rfind(" "),
        ]

        valid_boundaries = [
            position + 1
            for position in boundary_candidates
            if position >= int(max_chars * 0.6)
        ]

        if valid_boundaries:
            end = start + max(valid_boundaries)

        chunk = text[start:end].strip()

        if not chunk:
            end = start + max_chars
            chunk = text[start:end].strip()

        if len(chunk) > max_chars:
            raise ValueError(
                "Chunk size limit exceeded"
            )

        chunks.append(chunk)

        # Move forward while retaining a small overlap.
        next_start = end - overlap_chars

        if next_start <= start:
            next_start = end

        start = next_start

    if any(
        len(chunk) > max_chars
        for chunk in chunks
    ):
        raise ValueError(
            "One or more chunks exceed the size limit"
        )

    return chunks


# ==================================================
# 7. MERGE CHUNK RESULTS
# ==================================================

def merge_extraction_results(results):
    """Merge extracted entities and remove duplicates."""

    merged = {}
    output = []

    for result in results:

        for entity in result.entities:

            entity_data = entity.model_dump()

            entity_type = entity_data.get(
                "entity_type",
                "unknown",
            )

            name = entity_data.get("name")

            if not name:
                output.append(entity_data)
                continue

            identity = (
                entity_type,
                re.sub(
                    r"\s+",
                    " ",
                    name.strip().lower(),
                ),
            )

            if identity not in merged:

                merged[identity] = entity_data
                output.append(entity_data)

    return ExtractionResult.model_validate(
        {
            "entities": output,
        }
    )


# ==================================================
# 8. PROVIDER REQUEST WITH RETRIES
# ==================================================

def call_provider_with_retry(
    provider_function,
    source_text,
):
    """Retry rate limits and temporary server errors."""

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            with API_SEMAPHORE:

                return provider_function(source_text)

        except Exception as error:

            status = get_http_status(error)

            # HTTP 413 is handled by semantic chunking.
            if status == 413:
                raise

            retryable = (
                status == 429
                or status in (
                    500,
                    502,
                    503,
                    504,
                )
            )

            if not retryable:
                raise

            if attempt == MAX_RETRIES:
                raise

            delay = (
                2 ** (attempt - 1)
                + random.uniform(0, 0.5)
            )

            logger.warning(
                "HTTP %s received. "
                "Retry %s/%s in %.2f seconds.",
                status,
                attempt,
                MAX_RETRIES,
                delay,
            )

            time.sleep(delay)

    raise RuntimeError(
        "Provider retry attempts exhausted"
    )


# ==================================================
# 9. HANDLE HTTP 413 WITH CHUNKING
# ==================================================

def extract_with_chunking(
    provider_function,
    source_text,
    depth=0,
):
    """Split oversized requests and merge their results."""

    try:

        return call_provider_with_retry(
            provider_function,
            source_text,
        )

    except Exception as error:

        status = get_http_status(error)

        if status != 413:
            raise

        if depth >= MAX_CHUNK_DEPTH:

            raise RuntimeError(
                "Maximum chunking depth reached"
            ) from error

        logger.warning(
            "HTTP 413 detected. Splitting request. "
            "Depth: %s",
            depth + 1,
        )

        chunks = split_text_semantically(
            source_text
        )

        if len(chunks) <= 1:

            raise RuntimeError(
                "Request remains too large after splitting"
            ) from error

        logger.info(
            "Created %s semantic chunks",
            len(chunks),
        )

        results = []

        for index, chunk in enumerate(
            chunks,
            start=1,
        ):

            logger.info(
                "Processing chunk %s/%s",
                index,
                len(chunks),
            )

            result = extract_with_chunking(
                provider_function,
                chunk,
                depth + 1,
            )

            results.append(result)

        return merge_extraction_results(results)


# ==================================================
# 10. MAIN LLM FALLBACK MANAGER
# ==================================================

def extract_with_fallback(source_text):
    """
    Provider order:
    Gemini -> Groq -> DeepSeek (if configured).
    """

    if not source_text or not source_text.strip():

        raise ValueError(
            "Source text cannot be empty"
        )

    errors = []

    for provider in PROVIDERS:

        provider_name = provider["name"]

        provider_function = provider["function"]

        logger.info(
            "Trying LLM provider: %s",
            provider_name,
        )

        try:

            result = extract_with_chunking(
                provider_function,
                source_text,
            )

            if result is None:

                raise ValueError(
                    "Provider returned an empty result"
                )

            logger.info(
                "Extraction successful using %s",
                provider_name,
            )

            return {
                "success": True,
                "provider": provider_name,
                "extracted_at": datetime.now(
                    timezone.utc
                ).isoformat(),
                "data": result.model_dump(),
                "errors": errors,
            }

        except Exception as error:

            error_message = (
                f"{provider_name}: "
                f"{type(error).__name__}: {error}"
            )

            errors.append(error_message)

            logger.exception(
                "%s failed. Trying next provider.",
                provider_name,
            )

    logger.error(
        "All configured LLM providers failed"
    )

    return {
        "success": False,
        "provider": None,
        "extracted_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "data": None,
        "errors": errors,
    }


# ==================================================
# 11. BASIC MANAGER TEST
# ==================================================

if __name__ == "__main__":

    sample_text = """
    TechNova AI is an artificial intelligence startup.

    The company develops SmartWriter, an AI writing
    assistant that helps users create articles and
    business documents.

    Its official website is https://example.com.

    The article does not mention its pricing or launch date.
    """

    print("\nGRAPHONE AI RELIABLE LLM MANAGER")
    print("=" * 55)

    print("Available providers:")

    for provider in PROVIDERS:
        print("-", provider["name"])

    print("\nTesting semantic chunking...")

    chunks = split_text_semantically(
        sample_text,
        max_chars=500,
    )

    print("Test chunks:", len(chunks))

    print("\nStarting extraction...")

    result = extract_with_fallback(
        sample_text
    )

    print("\nFINAL RESULT")
    print("=" * 55)

    if result["success"]:

        print("Status: SUCCESS")
        print("Provider:", result["provider"])

        entities = result["data"]["entities"]

        print("Entities:", len(entities))

        for entity in entities:

            print(
                entity["entity_type"],
                "|",
                entity["name"],
            )

    else:

        print("Status: FAILED")

        for error in result["errors"]:
            print(error)

    print(
        "\nRELIABLE LLM MANAGER TEST COMPLETED"
    )
