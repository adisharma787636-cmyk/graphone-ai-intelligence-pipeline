
import pandas as pd
import requests
import time

INPUT_FILE = "data/exports/arxiv_papers.csv"

df = pd.read_csv(INPUT_FILE)
session = requests.Session()

print("TESTING 5 RESEARCH PAPERS")
print("=" * 60)

for _, row in df.head(5).iterrows():

    arxiv_id = str(row["arxiv_id"]).split("v")[0]

    try:
        response = session.get(
            f"https://paperswithcode.co/api/v1/papers/arxiv/{arxiv_id}",
            params={"include_resources": "true"},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            repositories = data.get("repositories") or []

            official_count = sum(
                1 for repo in repositories
                if repo.get("is_official")
            )

            stars = [
                repo.get("num_stars")
                for repo in repositories
            ]

            print(
                f"{arxiv_id} | HTTP 200 | "
                f"Repositories: {len(repositories)} | "
                f"Official: {official_count} | "
                f"Stars: {stars}"
            )

        else:
            print(arxiv_id, "| HTTP", response.status_code)

    except requests.RequestException as error:
        print(arxiv_id, "| ERROR:", error)

    time.sleep(1)

print("=" * 60)
print("TEST COMPLETED")
