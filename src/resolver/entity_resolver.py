
import csv
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

from rapidfuzz import fuzz, process


# ============================================================
# STEP 1: PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "llm_extractions.json"

OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "resolved_entities.json"

LOG_FILE = PROJECT_ROOT / "data" / "exports" / "entity_mapping_log.csv"


# ============================================================
# STEP 2: MATCHING CONFIGURATION
# ============================================================

AUTO_MATCH_THRESHOLD = 95
REVIEW_THRESHOLD = 80

SUPPORTED_TYPES = {
    "startup",
    "ai_product",
    "ai_hardware",
    "unknown"
}


# ============================================================
# STEP 3: 50 AI STARTUP SEEDS
# ============================================================

STARTUP_SEEDS = [
    "OpenAI", "Anthropic", "Google DeepMind", "Mistral AI",
    "Cohere", "Hugging Face", "Perplexity AI", "Scale AI",
    "Databricks", "Stability AI", "Runway", "Midjourney",
    "Character AI", "ElevenLabs", "Synthesia", "Pinecone",
    "LangChain", "Together AI", "Groq", "DeepSeek",
    "Inflection AI", "Adept AI", "Glean", "Harvey",
    "Anysphere", "Cursor", "Replit", "Windsurf",
    "Sakana AI", "AI21 Labs", "Writer", "Jasper",
    "Copy.ai", "Weights & Biases", "Modal", "Replicate",
    "Vercel", "Abridge", "NVIDIA", "Datadog",
    "Sierra", "Hume AI", "Physical Intelligence", "Figure AI",
    "Skild AI", "Thinking Machines Lab", "Safe Superintelligence",
    "Poolside", "Decagon", "Lovable"
]


# ============================================================
# STEP 4: KNOWN ALIASES
# ============================================================

ALIASES = {
    "open ai": "OpenAI",
    "deep mind": "Google DeepMind",
    "huggingface": "Hugging Face",
    "mistral": "Mistral AI",
    "character.ai": "Character AI",
    "eleven labs": "ElevenLabs",
    "stability": "Stability AI",
    "perplexity": "Perplexity AI",
    "ai21": "AI21 Labs",
    "weights and biases": "Weights & Biases"
}


# ============================================================
# STEP 5: NORMALIZE NAMES
# ============================================================

def normalize_name(name):

    if not isinstance(name, str) or not name.strip():
        return ""

    name = name.lower().strip()
    name = name.replace("&", " and ")
    name = re.sub(r"[^a-z0-9]+", " ", name)
    name = re.sub(r"\s+", " ", name)

    return name.strip()


# ============================================================
# STEP 6: NORMALIZE ENTITY TYPES
# ============================================================

def normalize_entity_type(entity_type, category=""):

    value = str(entity_type or "").strip().lower()
    category = str(category or "").strip().lower()

    if any(
        word in category
        for word in ("hardware", "chip", "gpu", "processor")
    ):
        return "ai_hardware"

    if value in ("startup", "company", "ai_startup"):
        return "startup"

    if value in ("ai_product", "product", "tool"):
        return "ai_product"

    if value in ("ai_hardware", "hardware", "chip"):
        return "ai_hardware"

    return "unknown"


# ============================================================
# STEP 7: KNOWN STARTUP MATCHING
# ============================================================

def get_canonical_startup_name(name):

    normalized = normalize_name(name)

    for alias, canonical in ALIASES.items():

        if normalize_name(alias) == normalized:
            return canonical

    for seed in STARTUP_SEEDS:

        if normalize_name(seed) == normalized:
            return seed

    return None


# ============================================================
# STEP 8: ENTITY RESOLUTION
# ============================================================

def resolve_entity(name, entity_type, canonical_names_by_type):

    normalized = normalize_name(name)

    if not normalized:

        return {
            "canonical_name": None,
            "match_score": 0.0,
            "match_status": "invalid_name"
        }

    if entity_type == "startup":

        known_name = get_canonical_startup_name(name)

        if known_name:

            return {
                "canonical_name": known_name,
                "match_score": 100.0,
                "match_status": "known_alias_or_seed"
            }

    canonical_names = canonical_names_by_type.get(entity_type, [])

    if not canonical_names:

        return {
            "canonical_name": name.strip(),
            "match_score": 100.0,
            "match_status": "new_entity"
        }

    choices = {
        normalize_name(item): item
        for item in canonical_names
    }

    match = process.extractOne(
        normalized,
        choices.keys(),
        scorer=fuzz.ratio,
        score_cutoff=REVIEW_THRESHOLD
    )

    if not match:

        return {
            "canonical_name": name.strip(),
            "match_score": 0.0,
            "match_status": "new_entity"
        }

    matched_normalized, score, _ = match

    canonical_name = choices[matched_normalized]

    if score >= AUTO_MATCH_THRESHOLD:

        return {
            "canonical_name": canonical_name,
            "match_score": round(score, 2),
            "match_status": "automatic_match"
        }

    return {
        "canonical_name": None,
        "suggested_name": canonical_name,
        "match_score": round(score, 2),
        "match_status": "manual_review"
    }


# ============================================================
# STEP 9: MAIN RESOLUTION PIPELINE
# ============================================================

def run_entity_resolution():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        articles = json.load(file)

    if not isinstance(articles, list):
        raise ValueError("Expected a JSON list of article records.")

    canonical_names_by_type = {
        "startup": list(STARTUP_SEEDS),
        "ai_product": [],
        "ai_hardware": [],
        "unknown": []
    }

    entity_groups = {}

    for article in articles:

        if not isinstance(article, dict):
            continue

        extraction = article.get("llm_result", {})

        if not isinstance(extraction, dict) or not extraction.get("success"):
            continue

        data = extraction.get("data", {})

        if not isinstance(data, dict):
            continue

        entities = data.get("entities", [])

        if not isinstance(entities, list):
            continue

        for entity in entities:

            if not isinstance(entity, dict):
                continue

            raw_name = entity.get("name")

            if not isinstance(raw_name, str) or not raw_name.strip():
                continue

            entity_type = normalize_entity_type(
                entity.get("entity_type"),
                entity.get("category")
            )

            identity = (
                entity_type,
                normalize_name(raw_name)
            )

            # Preserve every article reference.
            if identity not in entity_groups:

                entity_groups[identity] = {
                    "raw_name": raw_name.strip(),
                    "entity_type": entity_type,
                    "description": entity.get("description"),
                    "category": entity.get("category"),
                    "developer": entity.get("developer"),
                    "website_url": entity.get("website_url"),
                    "pricing_model": entity.get("pricing_model"),
                    "launch_date": entity.get("launch_date"),
                    "articles": []
                }

            group = entity_groups[identity]

            group["articles"].append({
                "article_title": article.get("article_title"),
                "article_url": article.get("article_url"),
                "source_name": article.get("source_name"),
                "published_at": article.get("published_at"),
                "provider": extraction.get("provider")
            })

            # Fill missing metadata from repeated occurrences.
            for field in (
                "description",
                "category",
                "developer",
                "website_url",
                "pricing_model",
                "launch_date"
            ):

                if not group.get(field) and entity.get(field):
                    group[field] = entity.get(field)

    resolved_entities = []
    mapping_logs = []

    for group in entity_groups.values():

        raw_name = group["raw_name"]
        entity_type = group["entity_type"]

        result = resolve_entity(
            raw_name,
            entity_type,
            canonical_names_by_type
        )

        match_status = result["match_status"]
        canonical_name = result.get("canonical_name")

        if match_status == "new_entity":

            canonical_name = raw_name

            canonical_names_by_type.setdefault(
                entity_type, []
            ).append(canonical_name)

        # ====================================================
        # STEP 9A: CLASSIFICATION REVIEW
        # ====================================================

        review_reasons = []

        if entity_type == "unknown":
            review_reasons.append("Unknown entity type")

        if raw_name.lower() == "os-level ai agent":
            review_reasons.append("Generic technology description")

        if entity_type == "ai_hardware":
            review_reasons.append(
                "Hardware entity; separate from software products"
            )

        if match_status == "manual_review":
            review_reasons.append(
                "Fuzzy match requires manual confirmation"
            )

        # ====================================================
        # STEP 9B: DATA QUALITY WARNINGS
        # ====================================================

        data_quality_flags = []

        if entity_type == "startup" and not group.get("website_url"):
            data_quality_flags.append(
                "Startup website not available"
            )

        if entity_type == "ai_product" and not group.get("website_url"):
            data_quality_flags.append(
                "Product website not available"
            )

        if not group.get("description"):
            data_quality_flags.append("Description not available")

        if not group.get("developer") and entity_type == "ai_product":
            data_quality_flags.append("Developer information not available")

        # ====================================================
        # STEP 9C: FINAL ENTITY RECORD
        # ====================================================

        record = {
            "raw_name": raw_name,
            "canonical_name": canonical_name,
            "entity_type": entity_type,
            "description": group["description"],
            "category": group["category"],
            "developer": group["developer"],
            "website_url": group["website_url"],
            "pricing_model": group["pricing_model"],
            "launch_date": group["launch_date"],
            "match_score": result["match_score"],
            "match_status": match_status,
            "review_reasons": review_reasons,
            "data_quality_flags": data_quality_flags,
            "articles": group["articles"],
            "article_count": len(group["articles"]),
            "resolved_at": datetime.now(timezone.utc).isoformat()
        }

        if result.get("suggested_name"):
            record["suggested_name"] = result["suggested_name"]

        resolved_entities.append(record)

        # ====================================================
        # STEP 9D: SOURCE MAPPING LOG
        # ====================================================

        for source in group["articles"]:

            log_record = {
                "raw_name": raw_name,
                "canonical_name": canonical_name,
                "entity_type": entity_type,
                "match_score": result["match_score"],
                "match_status": match_status,
                "review_reasons": "; ".join(review_reasons),
                "data_quality_flags": "; ".join(data_quality_flags),
                "article_title": source["article_title"],
                "article_url": source["article_url"],
                "source_name": source["source_name"],
                "provider": source["provider"],
                "suggested_name": result.get("suggested_name"),
                "resolved_at": record["resolved_at"]
            }

            mapping_logs.append(log_record)

    # ========================================================
    # STEP 10: SAVE JSON
    # ========================================================

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:

        json.dump(
            resolved_entities,
            file,
            indent=4,
            ensure_ascii=False
        )

    # ========================================================
    # STEP 11: SAVE CSV MAPPING LOG
    # ========================================================

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "raw_name",
        "canonical_name",
        "entity_type",
        "match_score",
        "match_status",
        "review_reasons",
        "data_quality_flags",
        "article_title",
        "article_url",
        "source_name",
        "provider",
        "suggested_name",
        "resolved_at"
    ]

    with open(
        LOG_FILE,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(mapping_logs)

    # ========================================================
    # STEP 12: SUMMARY
    # ========================================================

    automatic = sum(
        item["match_status"] in (
            "automatic_match",
            "known_alias_or_seed"
        )
        for item in resolved_entities
    )

    new = sum(
        item["match_status"] == "new_entity"
        for item in resolved_entities
    )

    manual_review = sum(
        item["match_status"] == "manual_review"
        or bool(item["review_reasons"])
        for item in resolved_entities
    )

    data_quality_warnings = sum(
        bool(item["data_quality_flags"])
        for item in resolved_entities
    )

    print("\n" + "=" * 60)
    print("       ENTITY RESOLUTION COMPLETED")
    print("=" * 60)

    print("Startup seeds:", len(STARTUP_SEEDS))
    print("Unique entities:", len(resolved_entities))
    print("Source mapping rows:", len(mapping_logs))
    print("Known/automatic matches:", automatic)
    print("New entities:", new)
    print("Entities requiring review:", manual_review)
    print("Entities with data-quality warnings:", data_quality_warnings)

    print("\nENTITY TYPE SUMMARY")

    for entity_type in sorted(SUPPORTED_TYPES):

        count = sum(
            item["entity_type"] == entity_type
            for item in resolved_entities
        )

        print(f"{entity_type}: {count}")

    print("\nOUTPUT FILES")
    print("JSON:", OUTPUT_FILE)
    print("CSV:", LOG_FILE)
    print("=" * 60)


# ============================================================
# STEP 13: RUN PROGRAM
# ============================================================

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s"
    )

    run_entity_resolution()
