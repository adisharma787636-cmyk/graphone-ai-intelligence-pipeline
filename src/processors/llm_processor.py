
import json
import logging
from pathlib import Path

from src.services.llm_manager import extract_with_fallback

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_FILE = PROJECT_ROOT / "data" / "raw" / "ai_news.json"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "llm_extractions.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)


def process_news_articles():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"News file not found: {INPUT_FILE}")

    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        articles = json.load(file)

    if not isinstance(articles, list):
        raise ValueError("Expected the news JSON file to contain a list.")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    results = []

    for index, article in enumerate(articles, start=1):
        title = article.get("title", "Untitled")
        article_text = article.get("article_text", "")

        print("\n" + "=" * 65)
        print(f"ARTICLE {index}/{len(articles)}")
        print(f"Title: {title}")
        print("=" * 65)

        if not article_text.strip():
            logging.warning("Skipping article with empty text: %s", title)
            continue

        # Send the real article text to the LLM manager
        extraction = extract_with_fallback(article_text)

        record = {
            "article_title": title,
            "article_url": article.get("url"),
            "source_name": article.get("source_name"),
            "published_at": article.get("published_at"),
            "text_source": article.get("text_source"),
            "llm_result": extraction
        }

        results.append(record)

        print("Success:", extraction.get("success"))
        print("Provider:", extraction.get("provider"))

        if extraction.get("success"):
            entities = extraction.get("data", {}).get("entities", [])
            print("Entities extracted:", len(entities))

            for entity in entities:
                print(
                    " -",
                    entity.get("entity_type"),
                    "|",
                    entity.get("name")
                )
        else:
            print("Extraction failed:", extraction.get("errors"))

        # Save progress after every article
        with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
            json.dump(results, file, indent=4, ensure_ascii=False)

    print("\n" + "=" * 65)
    print("LLM PROCESSING COMPLETED")
    print("Articles processed:", len(results))
    print("Output file:", OUTPUT_FILE)
    print("=" * 65)


if __name__ == "__main__":
    process_news_articles()
