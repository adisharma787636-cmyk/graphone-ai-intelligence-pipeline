
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


# ============================================================
# STEP 3: 50 AI STARTUP SEEDS
# ============================================================

STARTUP_SEEDS = [
    "OpenAI",
    "Anthropic",
    "Google DeepMind",
    "Mistral AI",
    "Cohere",
    "Hugging Face",
    "Perplexity AI",
    "Scale AI",
    "Databricks",
    "Stability AI",
    "Runway",
    "Midjourney",
    "Character AI",
    "ElevenLabs",
    "Synthesia",
    "Pinecone",
    "LangChain",
    "Together AI",
    "Groq",
    "DeepSeek",
    "Inflection AI",
    "Adept AI",
    "Glean",
    "Harvey",
    "Anysphere",
    "Cursor",
    "Replit",
    "Windsurf",
    "Sakana AI",
    "AI21 Labs",
    "Writer",
    "Jasper",
    "Copy.ai",
    "Weights & Biases",
    "Modal",
    "Replicate",
    "Vercel",
    "Abridge",
    "NVIDIA",
    "Datadog",
    "Sierra",
    "Hume AI",
    "Physical Intelligence",
    "Figure AI",
    "Skild AI",
    "Thinking Machines Lab",
    "Safe Superintelligence",
    "Poolside",
    "Decagon",
    "Lovable"
]


# ============================================================
# STEP 4: KNOWN STARTUP NAME ALIASES
# ============================================================

ALIASES = {
    "open ai": "OpenAI",
    "google deepmind": "Google DeepMind",
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
# STEP 5: NORMALIZE ENTITY NAMES
# ============================================================

def normalize_name(name):
    """Normalize names for reliable comparison."""

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

def normalize_entity_type(entity_type):
    """Convert entity types into consistent labels."""

    if not entity_type:
        return "unknown"

    entity_type = str(entity_type).strip().lower()

    if entity_type in ("startup", "company", "ai_startup"):
        return "startup"

    if entity_type in ("ai_product", "product", "tool"):
        return "ai_product"

    return entity_type


# ============================================================
# STEP 7: FIND KNOWN STARTUP NAMES
# ============================================================

def get_canonical_startup_name(name):
    """Resolve known startup aliases and seed names."""

    normalized = normalize_name(name)

    # Check known aliases.
    for alias, canonical in ALIASES.items():

        if normalize_name(alias) == normalized:
            return canonical

    # Check startup seed list.
    for seed in STARTUP_SEEDS:

        if normalize_name(seed) == normalized:
            return seed

    return None


# ============================================================
# STEP 8: TYPE-AWARE ENTITY RESOLUTION
# ============================================================

def resolve_entity(name, entity_type, canonical_names_by_type):
    """
    Match entities only against canonical names
    belonging to the same entity type.
    """

    normalized = normalize_name(name)

    if not normalized:
        return {
            "canonical_name": None,
            "match_score": 0.0,
            "match_status": "invalid_name"
        }

    entity_type = normalize_entity_type(entity_type)

    # --------------------------------------------------------
    # STARTUP: Check known aliases and seed names.
    # --------------------------------------------------------

    if entity_type == "startup":

        known_name = get_canonical_startup_name(name)

        if known_name:

            return {
                "canonical_name": known_name,
                "match_score": 100.0,
                "match_status": "known_alias_or_seed"
            }

    # --------------------------------------------------------
    # TYPE-AWARE MATCHING
    # --------------------------------------------------------

    canonical_names = canonical_names_by_type.get(
        entity_type,
        []
    )

    if not canonical_names:

        return {
            "canonical_name": name.strip(),
            "match_score": 100.0,
            "match_status": "new_entity"
        }

    # Create a mapping of normalized names to canonical names.
    choices = {
        normalize_name(canonical): canonical
        for canonical in canonical_names
    }

    match = process.extractOne(
        normalized,
        choices.keys(),
        scorer=fuzz.ratio,
        score_cutoff=REVIEW_THRESHOLD
    )

    # --------------------------------------------------------
    # NO MATCH FOUND
    # --------------------------------------------------------

    if not match:

        return {
            "canonical_name": name.strip(),
            "match_score": 0.0,
            "match_status": "new_entity"
        }

    matched_normalized, score, _ = match

    canonical_name = choices[matched_normalized]

    # --------------------------------------------------------
    # AUTOMATIC MATCH
    # --------------------------------------------------------

    if score >= AUTO_MATCH_THRESHOLD:

        return {
            "canonical_name": canonical_name,
            "match_score": round(score, 2),
            "match_status": "automatic_match"
        }

    # --------------------------------------------------------
    # MANUAL REVIEW
    # --------------------------------------------------------

    return {
        "canonical_name": None,
        "suggested_name": canonical_name,
        "match_score": round(score, 2),
        "match_status": "manual_review"
    }


# ============================================================
# STEP 9: MAIN ENTITY RESOLUTION PIPELINE
# ============================================================

def run_entity_resolution():

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    # --------------------------------------------------------
    # Load LLM extraction results.
    # --------------------------------------------------------

    with open(INPUT_FILE, "r", encoding="utf-8") as file:

        articles = json.load(file)

    if not isinstance(articles, list):

        raise ValueError(
            "Expected a JSON list containing article records."
        )

    # --------------------------------------------------------
    # Maintain separate canonical-name groups.
    # --------------------------------------------------------

    canonical_names_by_type = {
        "startup": list(STARTUP_SEEDS),
        "ai_product": [],
        "unknown": []
    }

    resolved_entities = []

    mapping_logs = []

    seen_entities = set()

    # --------------------------------------------------------
    # Process every article.
    # --------------------------------------------------------

    for article in articles:

        if not isinstance(article, dict):
            continue

        extraction = article.get("llm_result", {})

        if not isinstance(extraction, dict):
            continue

        if not extraction.get("success"):
            continue

        data = extraction.get("data", {})

        if not isinstance(data, dict):
            continue

        entities = data.get("entities", [])

        if not isinstance(entities, list):
            continue

        # ----------------------------------------------------
        # Process extracted entities.
        # ----------------------------------------------------

        for entity in entities:

            if not isinstance(entity, dict):
                continue

            raw_name = entity.get("name")

            if not isinstance(raw_name, str) or not raw_name.strip():
                continue

            entity_type = normalize_entity_type(
                entity.get("entity_type", "unknown")
            )

            identity = (
                entity_type,
                normalize_name(raw_name)
            )

            # Avoid processing identical raw names repeatedly.
            if identity in seen_entities:
                continue

            seen_entities.add(identity)

            # ------------------------------------------------
            # Resolve the entity.
            # ------------------------------------------------

            result = resolve_entity(
                raw_name,
                entity_type,
                canonical_names_by_type
            )

            match_status = result["match_status"]

            canonical_name = result.get("canonical_name")

            # ------------------------------------------------
            # Add new entities to their own type group.
            # ------------------------------------------------

            if match_status == "new_entity":

                canonical_name = raw_name.strip()

                group = canonical_names_by_type.setdefault(
                    entity_type,
                    []
                )

                if normalize_name(canonical_name) not in {
                    normalize_name(item) for item in group
                }:

                    group.append(canonical_name)

            # ------------------------------------------------
            # Prepare resolved record.
            # ------------------------------------------------

            resolved_record = {

                "raw_name": raw_name,

                "canonical_name": canonical_name,

                "entity_type": entity_type,

                "match_score": result["match_score"],

                "match_status": match_status,

                "article_title": article.get("article_title"),

                "article_url": article.get("article_url"),

                "resolved_at": datetime.now(
                    timezone.utc
                ).isoformat()

            }

            # Add suggested name for manual review.
            if match_status == "manual_review":

                resolved_record["suggested_name"] = (
                    result["suggested_name"]
                )

            resolved_entities.append(resolved_record)

            mapping_logs.append(resolved_record)

    # ========================================================
    # STEP 10: SAVE JSON OUTPUT
    # ========================================================

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            resolved_entities,
            file,
            indent=4,
            ensure_ascii=False
        )

    # ========================================================
    # STEP 11: EXPORT CSV MAPPING LOG
    # ========================================================

    LOG_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    fieldnames = [
        "raw_name",
        "canonical_name",
        "entity_type",
        "match_score",
        "match_status",
        "article_title",
        "article_url",
        "resolved_at",
        "suggested_name"
    ]

    with open(
        LOG_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(mapping_logs)

    # ========================================================
    # STEP 12: GENERATE SUMMARY
    # ========================================================

    automatic = sum(
        item["match_status"] in (
            "automatic_match",
            "known_alias_or_seed"
        )
        for item in resolved_entities
    )

    review = sum(
        item["match_status"] == "manual_review"
        for item in resolved_entities
    )

    new = sum(
        item["match_status"] == "new_entity"
        for item in resolved_entities
    )

    # ========================================================
    # STEP 13: DISPLAY RESULTS
    # ========================================================

    print("\n" + "=" * 60)

    print("          ENTITY RESOLUTION COMPLETED")

    print("=" * 60)

    print("Startup seed entries:", len(STARTUP_SEEDS))

    print(
        "Unique startup seeds:",
        len(set(STARTUP_SEEDS))
    )

    print(
        "Unique raw entities:",
        len(resolved_entities)
    )

    print(
        "Known/automatic matches:",
        automatic
    )

    print(
        "Manual reviews:",
        review
    )

    print(
        "New entities:",
        new
    )

    print("\nENTITY TYPE SUMMARY")

    for entity_type in sorted(canonical_names_by_type):

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
# STEP 14: RUN PROGRAM
# ============================================================

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s"
    )

    run_entity_resolution()
