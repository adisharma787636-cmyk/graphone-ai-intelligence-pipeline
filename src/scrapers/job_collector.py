
import asyncio
import csv
import hashlib
import json
import re
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import aiohttp
import feedparser

# ==========================================================
# CONFIGURATION
# ==========================================================

BASE_DIR = Path(__file__).resolve().parents[2]

JSON_FILE = BASE_DIR / "data" / "raw" / "ai_jobs.json"
CSV_FILE = BASE_DIR / "data" / "exports" / "ai_jobs.csv"

JOB_SOURCES = {
    "Remote OK": "https://remoteok.com/api",
    "Jobicy": "https://jobicy.com/api/v2/remote-jobs",
    "Arbeitnow": "https://www.arbeitnow.com/api/job-board-api",
    "Working Nomads": "https://www.workingnomads.com/api/exposed_jobs/",
    "We Work Remotely": "https://weworkremotely.com/remote-jobs.rss",
}

# Match role-related terms in titles, categories and tags.
AI_KEYWORDS = [
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "generative ai",
    "genai",
    "large language model",
    "llm",
    "data scientist",
    "data science",
    "computer vision",
    "natural language processing",
    "nlp",
    "ai engineer",
    "ml engineer",
    "ai researcher",
    "research scientist",
    "prompt engineer",
    "mlops",
    "ai developer",
    "neural network",
    "tensorflow",
    "pytorch",
    "robotics",
]

# Short abbreviations need word boundaries.
AI_SHORT_KEYWORDS = [
    r"\bAI\b",
    r"\bML\b",
    r"\bNLP\b",
    r"\bLLM\b",
]


# ==========================================================
# DATE NORMALIZATION
# ==========================================================

def parse_date(value):

    if value is None or value == "":
        return None

    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(
                value,
                tz=UTC
            )

        value = str(value).strip()

        # ISO date
        try:
            result = datetime.fromisoformat(
                value
            )

            if result.tzinfo is None:
                return None

            return result.astimezone(UTC)

        except ValueError:
            pass

        # RSS / RFC date
        try:
            result = parsedate_to_datetime(value)

            if result.tzinfo is None:
                return None

            return result.astimezone(UTC)

        except (TypeError, ValueError):
            return None

    except (ValueError, TypeError, OverflowError, OSError):
        return None


# ==========================================================
# URL NORMALIZATION
# ==========================================================

def normalize_url(url):

    if not url:
        return ""

    try:
        parts = urlsplit(url.strip())

        return urlunsplit((
            parts.scheme.lower(),
            parts.netloc.lower(),
            parts.path.rstrip("/"),
            "",
            ""
        ))

    except Exception:  # noqa: BLE001
        return url.strip()


# ==========================================================
# EXTRACT JOB RECORDS FROM JSON
# ==========================================================

def find_job_records(data):

    title_fields = [
        "title",
        "position",
        "jobTitle",
        "name"
    ]

    if isinstance(data, list):

        return [
            item for item in data
            if isinstance(item, dict)
            and any(item.get(field) for field in title_fields)
        ]

    if isinstance(data, dict):

        for key in ["jobs", "data", "results"]:

            value = data.get(key)

            if isinstance(value, list):
                records = find_job_records(value)

                if records:
                    return records

        for value in data.values():

            if isinstance(value, dict):
                records = find_job_records(value)

                if records:
                    return records

    return []


# ==========================================================
# AI / ML RELEVANCE FILTER
# ==========================================================

def is_ai_job(job):

    # Deliberately do not use the full description.
    # Incidental mentions of AI in a job description
    # can produce false positives.

    title = str(job.get("job_title") or "")
    category = str(job.get("category") or "")
    tags = str(job.get("tags") or "")

    searchable_text = (
        title + " " + category + " " + tags
    ).lower()

    for keyword in AI_KEYWORDS:

        if keyword in searchable_text:
            return True

    original_text = title + " " + category + " " + tags

    for pattern in AI_SHORT_KEYWORDS:

        if re.search(pattern, original_text, re.IGNORECASE):
            return True

    return False


# ==========================================================
# NORMALIZE JSON JOBS
# ==========================================================

def normalize_job(job, source_name, source_url):

    if source_name == "Remote OK":

        title = job.get("position") or job.get("title")
        company = job.get("company")
        location = job.get("location")
        description = job.get("description")
        published = job.get("date")
        application_url = (
            job.get("apply_url")
            or job.get("url")
            or job.get("original")
        )
        job_type = None
        tags = job.get("tags", [])
        category = None

    elif source_name == "Jobicy":

        title = job.get("jobTitle")
        company = job.get("companyName")
        location = job.get("jobGeo")
        description = (
            job.get("jobDescription")
            or job.get("jobExcerpt")
        )
        published = job.get("pubDate")
        application_url = job.get("url")
        job_type = job.get("jobType")
        tags = job.get("jobIndustry", [])
        category = job.get("jobIndustry")

    elif source_name == "Arbeitnow":

        title = job.get("title")
        company = job.get("company_name")
        location = job.get("location")
        description = job.get("description")
        published = job.get("created_at")
        application_url = job.get("url")
        job_type = job.get("job_types")
        tags = job.get("tags", [])
        category = None

    elif source_name == "Working Nomads":

        title = job.get("title")
        company = job.get("company_name")
        location = job.get("location")
        description = job.get("description")
        published = job.get("pub_date")
        application_url = job.get("url")
        job_type = None
        tags = job.get("tags", [])
        category = job.get("category_name")

    else:
        return None

    if not title:
        return None

    published_at = parse_date(published)

    if isinstance(tags, list):
        tags = ", ".join(str(tag) for tag in tags)

    if isinstance(category, list):
        category = ", ".join(str(item) for item in category)

    return {
        "job_title": str(title).strip(),
        "company": str(company).strip() if company else None,
        "location": str(location).strip() if location else None,
        "description": str(description).strip() if description else None,
        "application_url": application_url,
        "published_at": (
            published_at.isoformat()
            if published_at else None
        ),
        "job_type": job_type,
        "category": category,
        "tags": tags,
        "source_name": source_name,
        "source_url": source_url,
    }


# ==========================================================
# FETCH JSON SOURCE
# ==========================================================

async def fetch_json_source(session, source_name, url):

    async with session.get(url) as response:

        response.raise_for_status()

        data = await response.json(content_type=None)

        records = find_job_records(data)

        print(
            f"{source_name}: {len(records)} job records received"
        )

        normalized_jobs = []

        for record in records:

            job = normalize_job(
                record,
                source_name,
                url
            )

            if job:
                normalized_jobs.append(job)

        return normalized_jobs


# ==========================================================
# FETCH RSS SOURCE
# ==========================================================

async def fetch_rss_source(session, source_name, url):

    async with session.get(url) as response:

        response.raise_for_status()

        content = await response.text()

        feed = await asyncio.to_thread(
            feedparser.parse,
            content
        )

        jobs = []

        for entry in feed.entries:

            published = entry.get("published")

            published_at = parse_date(published)

            jobs.append({
                "job_title": entry.get("title"),
                "company": None,
                "location": None,
                "description": entry.get("summary"),
                "application_url": entry.get("link"),
                "published_at": (
                    published_at.isoformat()
                    if published_at else None
                ),
                "job_type": None,
                "category": None,
                "tags": "",
                "source_name": source_name,
                "source_url": url,
            })

        print(
            f"{source_name}: {len(jobs)} RSS entries received"
        )

        return jobs


# ==========================================================
# PROCESS ONE SOURCE
# ==========================================================

async def process_source(
    session,
    source_name,
    url,
    semaphore
):

    async with semaphore:

        print(f"\nProcessing: {source_name}")

        try:

            if source_name == "We Work Remotely":

                return await fetch_rss_source(
                    session,
                    source_name,
                    url
                )

            return await fetch_json_source(
                session,
                source_name,
                url
            )

        except Exception as error:  # noqa: BLE001

            print(
                f"{source_name} error: {error}"
            )

            return []


# ==========================================================
# FILTER FRESH JOBS
# ==========================================================

def filter_fresh_jobs(jobs):

    now = datetime.now(UTC)

    cutoff = now - timedelta(hours=24)

    fresh_jobs = []
    missing_dates = 0
    old_jobs = 0
    future_dates = 0

    for job in jobs:

        published = job.get("published_at")

        if not published:

            missing_dates += 1
            continue

        published_at = parse_date(published)

        if not published_at:

            missing_dates += 1
            continue

        if published_at > now:

            future_dates += 1
            continue

        if cutoff <= published_at <= now:

            job["published_at"] = published_at.isoformat()
            fresh_jobs.append(job)

        else:

            old_jobs += 1

    print("\nDATE FILTER RESULTS")
    print("Missing or invalid dates:", missing_dates)
    print("Outside last 24 hours:", old_jobs)
    print("Future dates:", future_dates)
    print("Fresh jobs:", len(fresh_jobs))

    return fresh_jobs


# ==========================================================
# REMOVE DUPLICATES
# ==========================================================

def remove_duplicates(jobs):

    unique_jobs = []
    seen = set()

    for job in jobs:

        url = normalize_url(
            job.get("application_url")
        )

        if url:

            unique_key = url

        else:

            raw_key = (
                str(job.get("job_title", "")).lower()
                + "|"
                + str(job.get("company", "")).lower()
            )

            unique_key = hashlib.sha256(
                raw_key.encode("utf-8")
            ).hexdigest()

        if unique_key in seen:
            continue

        seen.add(unique_key)
        unique_jobs.append(job)

    return unique_jobs


# ==========================================================
# SAVE JSON AND CSV
# ==========================================================

def save_results(jobs):

    JSON_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    CSV_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        JSON_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            jobs,
            file,
            indent=4,
            ensure_ascii=False
        )

    fields = [
        "job_id",
        "job_title",
        "company",
        "location",
        "description",
        "application_url",
        "source_name",
        "source_url",
        "published_at",
        "collected_at",
        "job_type",
        "category",
        "tags",
    ]

    with open(
        CSV_FILE,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields
        )

        writer.writeheader()

        for job in jobs:
            writer.writerow(job)

    print("\nFILES SAVED")
    print("JSON:", JSON_FILE)
    print("CSV:", CSV_FILE)


# ==========================================================
# MAIN FUNCTION
# ==========================================================

async def main():

    print("=" * 60)
    print("       GRAPHONE AI JOB COLLECTOR")
    print("=" * 60)

    timeout = aiohttp.ClientTimeout(total=40)

    headers = {
        "User-Agent": "GraphOneAI-Research-Project/1.0"
    }

    semaphore = asyncio.Semaphore(3)

    async with aiohttp.ClientSession(
        timeout=timeout,
        headers=headers
    ) as session:

        tasks = [
            process_source(
                session,
                source_name,
                url,
                semaphore
            )
            for source_name, url in JOB_SOURCES.items()
        ]

        results = await asyncio.gather(*tasks)

    all_jobs = [
        job
        for source_jobs in results
        for job in source_jobs
    ]

    print("\nTotal jobs collected:", len(all_jobs))

    # Filter AI / ML jobs using role information
    ai_jobs = [
        job for job in all_jobs
        if is_ai_job(job)
    ]

    print("AI / ML job matches:", len(ai_jobs))

    # Strict publication date filter
    fresh_jobs = filter_fresh_jobs(ai_jobs)

    # Remove duplicate listings
    unique_jobs = remove_duplicates(fresh_jobs)

    collected_at = datetime.now(
        UTC
    ).isoformat()

    for job in unique_jobs:

        job["collected_at"] = collected_at

        unique_key = (
            str(job.get("application_url") or "")
            + "|"
            + str(job.get("job_title") or "")
            + "|"
            + str(job.get("company") or "")
        )

        job["job_id"] = hashlib.sha256(
            unique_key.encode("utf-8")
        ).hexdigest()[:16]

    # Export
    save_results(unique_jobs)

    print("\n" + "=" * 60)
    print("       JOB COLLECTION COMPLETED")
    print("=" * 60)

    print("Sources monitored:", len(JOB_SOURCES))
    print("Total jobs collected:", len(all_jobs))
    print("AI / ML matches:", len(ai_jobs))
    print("Fresh AI jobs:", len(fresh_jobs))
    print("Unique fresh jobs:", len(unique_jobs))

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
