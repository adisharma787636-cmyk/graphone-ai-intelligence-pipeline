
import csv
import datetime
import json
import urllib.parse
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]

SOURCE_FILE = Path.home() / "Downloads" / "labspie-companies.csv"

JSON_OUTPUT = PROJECT_ROOT / "data" / "raw" / "ai_startups.json"
CSV_OUTPUT = PROJECT_ROOT / "data" / "exports" / "ai_startups.csv"


def normalize_website(url):
    """Normalize a website URL for duplicate checking."""
    if not url or not url.strip():
        return None

    url = url.strip().lower()

    if "://" not in url:
        url = "https://" + url

    parts = urllib.parse.urlsplit(url)

    # Ignore www and trailing slash differences
    hostname = (parts.hostname or "").removeprefix("www.")

    if not hostname:
        return url.rstrip("/")

    return hostname


def collect_startups():

    print("=" * 55)
    print("       GRAPHONE AI STARTUP COLLECTOR")
    print("=" * 55)

    if not SOURCE_FILE.exists():
        print("ERROR: Source CSV file not found:", SOURCE_FILE)
        return

    startups = []
    seen_websites = set()

    missing_websites = 0
    duplicate_websites = 0

    with open(
        SOURCE_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            # Select AI-native startups only
            if row["type"].strip().lower() != "startup":
                continue

            if row["ai_native"].strip().lower() != "yes":
                continue

            website = row["website"].strip()
            profile_url = row["profile_url"].strip()

            if not row["name"].strip():
                continue

            normalized_website = normalize_website(website)

            # Count missing websites but retain the record
            if not normalized_website:
                missing_websites += 1

            # Remove confirmed duplicate websites
            elif normalized_website in seen_websites:
                duplicate_websites += 1
                continue

            else:
                seen_websites.add(normalized_website)

            startup = {
                "startup_id": len(startups) + 1,
                "company_name": row["name"].strip(),
                "website": website if website else None,
                "normalized_website": normalized_website,
                "profile_url": profile_url if profile_url else None,
                "industry": row["field"].strip() or None,
                "ai_native": row["ai_native"].strip().lower(),
                "company_type": row["type"].strip().lower(),
                "founded_year": row["started"].strip() or None,
                "city": row["city"].strip() or None,
                "country": row["country"].strip() or None,
                "country_code": row["country_code"].strip() or None,
                "verified": row["verified"].strip().lower() == "yes",
                "source_name": "Labspie Open Data",
                "source_url": profile_url if profile_url else None,
                "collected_at": datetime.datetime.now(datetime.UTC).isoformat()
            }

            startups.append(startup)

    # Create output directories
    JSON_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    CSV_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    # Save JSON
    with open(JSON_OUTPUT, "w", encoding="utf-8") as file:
        json.dump(startups, file, indent=4, ensure_ascii=False)

    # Save CSV
    if startups:
        with open(CSV_OUTPUT, "w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=startups[0].keys()
            )
            writer.writeheader()
            writer.writerows(startups)

    verified_count = sum(item["verified"] for item in startups)

    print("\nSTARTUP COLLECTION COMPLETED")
    print("-" * 55)
    print("Total unique startup records:", len(startups))
    print("Missing websites:", missing_websites)
    print("Duplicate websites removed:", duplicate_websites)
    print("Labspie verified records:", verified_count)
    print("JSON file:", JSON_OUTPUT)
    print("CSV file:", CSV_OUTPUT)
    print("=" * 55)


if __name__ == "__main__":
    collect_startups()
