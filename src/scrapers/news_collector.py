
import asyncio
import calendar
import csv
import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import aiohttp
import feedparser
from bs4 import BeautifulSoup

# --------------------------------------------------
# PROJECT CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

JSON_OUTPUT = PROJECT_ROOT / "data" / "raw" / "ai_news.json"
CSV_OUTPUT = PROJECT_ROOT / "data" / "exports" / "ai_news.csv"

NEWS_SOURCES = {
    "OpenAI": "https://openai.com/news/rss.xml",

    "Google DeepMind":
        "https://deepmind.google/blog/rss.xml",

    "Hugging Face":
        "https://huggingface.co/blog/feed.xml",

    "TechCrunch AI":
        "https://techcrunch.com/category/artificial-intelligence/feed/",

    "MIT Technology Review":
        "https://www.technologyreview.com/topic/artificial-intelligence/feed"
}

HEADERS = {
    "User-Agent": "GraphOneAINewsCollector/1.0"
}

MAX_CONCURRENT_REQUESTS = 5
REQUEST_TIMEOUT = 25


# --------------------------------------------------
# STEP 1: NORMALIZE ARTICLE URL
# --------------------------------------------------

def normalize_url(url):

    if not url:
        return None

    parts = urlsplit(url.strip())

    # Remove tracking parameters and fragments
    return urlunsplit((
        parts.scheme.lower(),
        parts.netloc.lower(),
        parts.path.rstrip("/"),
        "",
        ""
    ))


# --------------------------------------------------
# STEP 2: PARSE PUBLICATION DATE
# --------------------------------------------------

def parse_publication_date(entry):

    published = entry.get("published_parsed")

    # Do not substitute updated_parsed.
    # Updated date is not necessarily publication date.

    if not published:
        return None

    try:
        timestamp = calendar.timegm(published)

        return datetime.fromtimestamp(
            timestamp,
            UTC
        )

    except (ValueError, OverflowError, OSError):
        return None


# --------------------------------------------------
# STEP 3: EXTRACT TEXT FROM RSS ENTRY
# --------------------------------------------------

def extract_rss_text(entry):

    content = []

    if entry.get("summary"):
        content.append(entry["summary"])

    for item in entry.get("content", []):
        if item.get("value"):
            content.append(item["value"])

    if not content:
        return None

    soup = BeautifulSoup(" ".join(content), "html.parser")

    return soup.get_text(" ", strip=True)


# --------------------------------------------------
# STEP 4: FETCH FULL ARTICLE TEXT
# --------------------------------------------------

async def fetch_article(session, url, semaphore):

    async with semaphore:

        try:
            async with session.get(
                url,
                headers=HEADERS,
                timeout=aiohttp.ClientTimeout(
                    total=REQUEST_TIMEOUT
                ),
                allow_redirects=True
            ) as response:

                if response.status != 200:
                    return None

                html = await response.text()

                soup = BeautifulSoup(html, "lxml")

                # Remove irrelevant page elements
                for element in soup.select(
                    "script, style, nav, footer, header, "
                    "aside, form, noscript"
                ):
                    element.decompose()

                # Find the main article
                article = soup.find("article")

                if article:
                    target = article
                else:
                    target = soup.find("main") or soup.body

                if not target:
                    return None

                paragraphs = target.find_all(
                    ["p", "h1", "h2", "h3"]
                )

                text = " ".join(
                    p.get_text(" ", strip=True)
                    for p in paragraphs
                )

                text = re.sub(r"\s+", " ", text).strip()

                if len(text) < 100:
                    return None

                return text

        except (TimeoutError, aiohttp.ClientError, ValueError):
            return None


# --------------------------------------------------
# STEP 5: PROCESS ONE NEWS SOURCE
# --------------------------------------------------

async def process_source(
    session,
    source_name,
    feed_url,
    now,
    semaphore
):

    print(f"\nProcessing: {source_name}")

    feed = await asyncio.to_thread(
        feedparser.parse,
        feed_url
    )

    results = []

    total_entries = len(feed.entries)
    missing_dates = 0
    outside_window = 0
    candidates = []

    cutoff = now - timedelta(hours=24)

    for entry in feed.entries:

        published_date = parse_publication_date(entry)

        # Exclude unknown publication dates
        if published_date is None:
            missing_dates += 1
            continue

        # Exclude old and future articles
        if not cutoff <= published_date <= now:
            outside_window += 1
            continue

        title = entry.get("title", "").strip()
        original_url = entry.get("link", "").strip()

        normalized_url = normalize_url(original_url)

        if not title or not normalized_url:
            continue

        candidates.append({
            "title": title,
            "url": original_url,
            "normalized_url": normalized_url,
            "published_at": published_date.isoformat(),
            "rss_text": extract_rss_text(entry)
        })

    # Fetch article pages asynchronously
    tasks = [
        fetch_article(
            session,
            item["url"],
            semaphore
        )
        for item in candidates
    ]

    article_texts = await asyncio.gather(*tasks)

    for item, full_text in zip(candidates, article_texts):

        # Prefer extracted article text.
        # RSS text is a fallback, not guaranteed full text.
        article_text = full_text or item["rss_text"]

        if not article_text:
            article_text = ""

        results.append({
            "title": item["title"],
            "url": item["url"],
            "normalized_url": item["normalized_url"],
            "source_name": source_name,
            "published_at": item["published_at"],
            "article_text": article_text,
            "text_source": (
                "full_article"
                if full_text
                else "rss_excerpt"
                if article_text
                else "unavailable"
            ),
            "full_text_extracted": bool(full_text),
            "collected_at": now.isoformat()
        })

    print("Total RSS entries:", total_entries)
    print("Missing publication dates:", missing_dates)
    print("Outside last 24 hours:", outside_window)
    print("Fresh article candidates:", len(candidates))
    print("Articles processed:", len(results))

    return results


# --------------------------------------------------
# STEP 6: COLLECT FROM ALL FIVE SOURCES
# --------------------------------------------------

async def collect_news():

    print("=" * 60)
    print("          GRAPHONE AI NEWS COLLECTOR")
    print("=" * 60)

    now = datetime.now(UTC)

    semaphore = asyncio.Semaphore(
        MAX_CONCURRENT_REQUESTS
    )

    connector = aiohttp.TCPConnector(
        limit=MAX_CONCURRENT_REQUESTS
    )

    all_articles = []

    async with aiohttp.ClientSession(
        connector=connector
    ) as session:

        tasks = [
            process_source(
                session,
                source_name,
                feed_url,
                now,
                semaphore
            )
            for source_name, feed_url in NEWS_SOURCES.items()
        ]

        source_results = await asyncio.gather(
            *tasks,
            return_exceptions=True
        )

        for result in source_results:

            if isinstance(result, Exception):
                print("SOURCE ERROR:", str(result))
                continue

            all_articles.extend(result) # type: ignore

    # --------------------------------------------------
    # STEP 7: REMOVE DUPLICATE ARTICLES
    # --------------------------------------------------

    unique_articles = []
    seen_urls = set()

    for article in all_articles:

        url = article["normalized_url"]

        if url in seen_urls:
            continue

        seen_urls.add(url)
        unique_articles.append(article)

    # Sort newest first
    unique_articles.sort(
        key=lambda item: item["published_at"],
        reverse=True
    )

    # --------------------------------------------------
    # STEP 8: SAVE JSON AND CSV
    # --------------------------------------------------

    JSON_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    CSV_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(  # noqa: ASYNC230
        JSON_OUTPUT,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            unique_articles,
            file,
            indent=4,
            ensure_ascii=False
        )

    fieldnames = [
        "title",
        "url",
        "normalized_url",
        "source_name",
        "published_at",
        "article_text",
        "text_source",
        "full_text_extracted",
        "collected_at"
    ]

    with open(  # noqa: ASYNC230
        CSV_OUTPUT,
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(unique_articles)

    # --------------------------------------------------
    # STEP 9: FINAL REPORT
    # --------------------------------------------------

    full_text_count = sum(
        item["full_text_extracted"]
        for item in unique_articles
    )

    print("\n" + "=" * 60)
    print("          NEWS COLLECTION COMPLETED")
    print("=" * 60)

    print("Sources monitored:", len(NEWS_SOURCES))
    print("Fresh articles before deduplication:", len(all_articles))
    print("Unique fresh articles:", len(unique_articles))
    print("Full article text extracted:", full_text_count)
    print("RSS excerpt or unavailable text:", len(unique_articles) - full_text_count)

    print("\nJSON file:", JSON_OUTPUT)
    print("CSV file:", CSV_OUTPUT)

    print("=" * 60)


# --------------------------------------------------
# MAIN
# --------------------------------------------------

if __name__ == "__main__":
    asyncio.run(collect_news())
