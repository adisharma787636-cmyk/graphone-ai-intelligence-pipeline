
import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path

import huggingface_hub
import pandas as pd

# ==================================================
# 1. PROJECT CONFIGURATION
# ==================================================

BASE_DIR = Path(__file__).resolve().parents[2]

RAW_DIR = BASE_DIR / "data" / "raw"
EXPORT_DIR = BASE_DIR / "data" / "exports"

JSON_FILE = RAW_DIR / "ai_products.json"
CSV_FILE = EXPORT_DIR / "ai_products.csv"

MIN_RELEVANCE = 0.0

EXCLUDED_TAGS = {
    "not-for-all-audiences",
}


# ==================================================
# 2. AI APPLICATION SEARCH CATEGORIES
# ==================================================

QUERIES = [
    "AI writing assistant",
    "AI image generator",
    "AI video generator",
    "AI coding assistant",
    "AI voice and text to speech",
    "AI data analysis",
    "AI document question answering",
    "AI education tutor",
    "AI translation",
    "AI chatbot",
    "AI speech recognition",
    "AI music generation",
    "AI 3D model generation",
    "AI OCR document processing",
    "AI text summarization",
    "AI autonomous agents",
    "AI recommendation system",
    "AI image editing",
    "AI object detection",
    "AI SQL assistant",
    "AI cybersecurity",
    "AI healthcare assistant",
    "AI finance assistant",
    "AI legal assistant",
    "AI agriculture",
    "AI robotics",
    "AI video understanding",
    "AI image captioning",
    "AI speech translation",
    "AI workflow automation",
]


# ==================================================
# 3. LOGGING CONFIGURATION
# ==================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# ==================================================
# 4. CONVERT SEARCH RESULT INTO A RECORD
# ==================================================

def convert_to_record(space):

    tags = list(space.tags or [])

    # Accept only records confirmed as public
    if space.private is not False:
        return None

    # Exclude unsuitable applications
    if EXCLUDED_TAGS.intersection(tags):
        return None

    # Check relevance score
    relevance = space.semantic_relevancy_score

    if relevance is None or relevance < MIN_RELEVANCE:
        return None

    # Validate application identity
    if not space.id or not space.title:
        return None

    # Hugging Face application URL
    space_url = (
        f"https://huggingface.co/spaces/{space.id}"
    )

    # Prepare record
    record = {
        "product_id": space.id,
        "product_name": space.title,
        "description": space.ai_short_description,
        "category": space.ai_category,
        "developer": space.author,

        "website_url": space_url,

        "source_name": "Hugging Face Spaces",
        "source_url": space_url,

        "pricing_model": None,
        "launch_date": None,

        "platform": space.sdk,

        "collected_at": datetime.now(UTC).isoformat(),

        "likes": space.likes,
        "trending_score": space.trending_score,
        "relevance_score": relevance,

        "tags": tags,
        "emoji": space.emoji,

        "private": space.private,

        "runtime_stage": (
            space.runtime.stage
            if space.runtime
            else None
        ),

        "discovered_by": [],
    }

    return record


# ==================================================
# 5. COLLECT AI APPLICATIONS
# ==================================================

def collect_ai_products():

    api = huggingface_hub.HfApi()

    products = {}

    logger.info(
        "Starting AI application collection..."
    )

    logger.info(
        "Total search categories: %s",
        len(QUERIES)
    )

    for index, query in enumerate(QUERIES, start=1):

        logger.info(
            "Processing category %s/%s: %s",
            index,
            len(QUERIES),
            query
        )

        try:

            results = api.search_spaces(
                query,
                include_non_running=True
            )

            category_count = 0

            for space in results:

                record = convert_to_record(space)

                if record is None:
                    continue

                product_id = record["product_id"]

                # Remove duplicate applications
                if product_id not in products:

                    products[product_id] = record

                # Preserve all discovery categories
                if query not in products[product_id]["discovered_by"]:

                    products[product_id]["discovered_by"].append(
                        query
                    )

                category_count += 1

            logger.info(
                "%s | Accepted: %s | Total unique: %s",
                query,
                category_count,
                len(products)
            )

        except Exception:

            logger.exception(
                "Error searching category '%s'",
                query
            )

        # Pause between API searches
        time.sleep(1)

    return list(products.values())


# ==================================================
# 6. SAVE DATA AS JSON AND CSV
# ==================================================

def save_products(products):

    # Create directories if they do not exist
    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    EXPORT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # Save JSON file
    with open(
        JSON_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            products,
            file,
            indent=4,
            ensure_ascii=False
        )

    # Save CSV file
    dataframe = pd.DataFrame(products)

    dataframe.to_csv(
        CSV_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    logger.info(
        "JSON file saved: %s",
        JSON_FILE
    )

    logger.info(
        "CSV file saved: %s",
        CSV_FILE
    )


# ==================================================
# 7. MAIN FUNCTION
# ==================================================

def main():

    products = collect_ai_products()

    save_products(products)

    print("\n" + "=" * 55)
    print("       AI APPLICATION COLLECTION COMPLETED")
    print("=" * 55)

    print(
        "\nTotal unique records:",
        len(products)
    )

    print(
        "\nJSON file:",
        JSON_FILE
    )

    print(
        "\nCSV file:",
        CSV_FILE
    )

    if len(products) >= 1000:

        print(
            "\nSUCCESS: The 1,000-record target has been reached!"
        )

    else:

        print(
            "\nRecords still required:",
            1000 - len(products)
        )

    print("=" * 55)


# ==================================================
# 8. PROGRAM ENTRY POINT
# ==================================================

if __name__ == "__main__":
    main()
