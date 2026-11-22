
import asyncio

import aiohttp
import feedparser

JOB_SOURCES = {
    "Remote OK": "https://remoteok.com/api",
    "Jobicy": "https://jobicy.com/api/v2/remote-jobs",
    "Arbeitnow": "https://www.arbeitnow.com/api/job-board-api",
    "Working Nomads": "https://www.workingnomads.com/api/exposed_jobs/",
    "We Work Remotely": "https://weworkremotely.com/remote-jobs.rss",
}

TITLE_FIELDS = [
    "title", "position", "jobTitle", "name"
]

DATE_FIELDS = [
    "date", "created_at", "pubDate", "pub_date",
    "publication_date", "published_at", "created"
]


async def inspect_source(session, name, url):
    print("\n" + "=" * 55)
    print("SOURCE:", name)

    try:
        async with session.get(url) as response:
            print("HTTP Status:", response.status)

            if response.status != 200:
                print("Could not access source.")
                return

            content = await response.text()

            if url.endswith(".rss"):
                feed = await asyncio.to_thread(feedparser.parse, content)

                print("Format: RSS")
                print("Total entries:", len(feed.entries))

                if feed.entries:
                    job = feed.entries[0]
                    print("Sample title:", job.get("title"))
                    print("Publication date:", job.get("published"))
                    print("Job URL:", job.get("link"))

                return

            data = await response.json(content_type=None)

            if isinstance(data, list):
                jobs = [
                    item for item in data
                    if isinstance(item, dict)
                    and any(item.get(field) for field in TITLE_FIELDS)
                ]

            elif isinstance(data, dict):
                jobs = data.get("jobs", data.get("data", []))

                if not isinstance(jobs, list):
                    jobs = []

            else:
                jobs = []

            print("Format: JSON")
            print("Actual job records:", len(jobs))

            if not jobs:
                print("No job records found.")
                return

            job = jobs[0]

            print("Available fields:", list(job.keys()))

            title = next(
                (job.get(field) for field in TITLE_FIELDS if job.get(field)),
                "Not found"
            )

            date = next(
                (job.get(field) for field in DATE_FIELDS if job.get(field)),
                "Not found"
            )

            print("Sample job title:", title)
            print("Publication date field:", date)

            print(
                "Date field names found:",
                [field for field in DATE_FIELDS if job.get(field)]
            )

    except Exception as error:  # noqa: BLE001
        print("Error:", str(error))


async def main():
    timeout = aiohttp.ClientTimeout(total=30)

    headers = {
        "User-Agent": "GraphOneAI-Research-Project/1.0"
    }

    async with aiohttp.ClientSession(
        timeout=timeout,
        headers=headers
    ) as session:

        await asyncio.gather(*[
            inspect_source(session, name, url)
            for name, url in JOB_SOURCES.items()
        ])


if __name__ == "__main__":
    asyncio.run(main())
