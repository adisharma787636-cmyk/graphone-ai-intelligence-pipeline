
import time
from pathlib import Path

import pandas as pd
import requests


# ==================================================
# GRAPHONE AI - ARXIV GITHUB ENRICHMENT
# ==================================================

INPUT_FILE = Path("data/exports/arxiv_papers.csv")
OUTPUT_FILE = Path("data/exports/arxiv_papers_enriched.csv")

API_URL = "https://paperswithcode.co/api/v1/papers/arxiv/"

REQUEST_DELAY = 1.0
TIMEOUT = 30
SAVE_EVERY = 25
MAX_RETRIES = 3


# ==================================================
# API SESSION
# ==================================================

session = requests.Session()

session.headers.update({
    "User-Agent": "GraphOne-AI-Research-Enrichment/1.0"
})


# ==================================================
# FETCH PAPER INFORMATION
# ==================================================

def fetch_repositories(arxiv_id):

    url = API_URL + arxiv_id

    for attempt in range(MAX_RETRIES):

        try:

            response = session.get(
                url,
                params={"include_resources": "true"},
                timeout=TIMEOUT
            )

            if response.status_code == 404:

                return {
                    "status": "not_found",
                    "repositories": []
                }

            if response.status_code == 429:

                wait_time = 2 ** attempt

                print(
                    f"Rate limited. Waiting {wait_time} seconds..."
                )

                time.sleep(wait_time)
                continue

            response.raise_for_status()

            data = response.json()

            return {
                "status": "found",
                "repositories": data.get("repositories") or []
            }

        except requests.RequestException as error:

            print(
                f"Request attempt {attempt + 1} failed: {error}"
            )

            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)

        except ValueError as error:

            print("Invalid API response:", error)

            return {
                "status": "error",
                "repositories": []
            }

    return {
        "status": "error",
        "repositories": []
    }


# ==================================================
# EXTRACT GITHUB INFORMATION
# ==================================================

def extract_repository_details(repositories):

    github_repositories = []
    repository_names = []
    star_values = []

    official_urls = []
    official_stars = []

    for repo in repositories:

        repo_url = repo.get("url") or ""

        if "github.com/" not in repo_url.lower():
            continue

        owner = repo.get("owner") or ""
        name = repo.get("name") or ""

        if owner and name:
            repository_name = f"{owner}/{name}"
        else:
            repository_name = name

        stars = repo.get("num_stars")

        is_official = bool(
            repo.get("is_official", False)
        )

        github_repositories.append(repo_url)

        repository_names.append(repository_name)

        star_values.append(
            "" if stars is None else str(stars)
        )

        if is_official:

            official_urls.append(repo_url)

            official_stars.append(
                "" if stars is None else str(stars)
            )

    return {

        "github_repositories": "; ".join(
            github_repositories
        ),

        "github_repository_names": "; ".join(
            repository_names
        ),

        "github_stars": "; ".join(
            star_values
        ),

        "official_repository": (
            "Yes" if official_urls else "No"
        ),

        "official_github_url": "; ".join(
            official_urls
        ),

        "official_github_stars": "; ".join(
            official_stars
        ),

        "repository_count": len(
            github_repositories
        ),

        "official_repository_count": len(
            official_urls
        )
    }


# ==================================================
# PREPARE DATAFRAME
# ==================================================

def prepare_dataframe(df):

    text_columns = [

        "github_repositories",
        "github_repository_names",
        "github_stars",
        "official_repository",
        "official_github_url",
        "official_github_stars",
        "paperswithcode_status"

    ]

    numeric_columns = [

        "repository_count",
        "official_repository_count"

    ]

    for column in text_columns:

        if column not in df.columns:

            df[column] = ""

        else:

            df[column] = (
                df[column]
                .fillna("")
                .astype("object")
            )

    for column in numeric_columns:

        if column not in df.columns:

            df[column] = 0

        else:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            ).fillna(0).astype("int64")

    return df


# ==================================================
# SAVE PROGRESS
# ==================================================

def save_progress(df):

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )


# ==================================================
# MAIN PROCESS
# ==================================================

def main():

    print("\n")

    print("=" * 65)
    print("       GRAPHONE AI - GITHUB METRICS ENRICHMENT")
    print("=" * 65)

    if not INPUT_FILE.exists():

        print("\nERROR: Input CSV not found:")
        print(INPUT_FILE.resolve())

        return

    # Read original dataset
    df = pd.read_csv(INPUT_FILE)

    print("\nTotal research papers:", len(df))

    if "arxiv_id" not in df.columns:

        print("ERROR: arxiv_id column is missing.")

        return

    df = prepare_dataframe(df)

    # Resume from an existing output file
    if OUTPUT_FILE.exists():

        existing = pd.read_csv(OUTPUT_FILE)

        if (
            len(existing) == len(df)
            and existing["arxiv_id"].astype(str).tolist()
            == df["arxiv_id"].astype(str).tolist()
        ):

            existing = prepare_dataframe(existing)

            df = existing

            print(
                "\nExisting enrichment found."
            )

            print(
                "Completed records will be skipped."
            )

    # Counters
    found = 0
    not_found = 0
    errors = 0

    total = len(df)

    # Process papers
    for index, row in df.iterrows():

        arxiv_id = str(
            row["arxiv_id"]
        ).strip()

        # Remove version suffix
        arxiv_id = arxiv_id.split("v")[0]

        current_status = str(
            df.at[index, "paperswithcode_status"]
        )

        # Skip previously completed records
        if current_status in ("found", "not_found"):

            if current_status == "found":
                found += 1

            else:
                not_found += 1

            continue

        print(
            f"\n[{index + 1}/{total}] "
            f"Processing: {arxiv_id}"
        )

        result = fetch_repositories(arxiv_id)

        repositories = result["repositories"]

        details = extract_repository_details(
            repositories
        )

        # Store repository information
        for column, value in details.items():

            df.at[index, column] = value

        df.at[index, "paperswithcode_status"] = (
            result["status"]
        )

        # Update counters
        if result["status"] == "found":

            found += 1

            print(
                "Repositories:",
                details["repository_count"]
            )

            print(
                "Official repositories:",
                details["official_repository_count"]
            )

            print(
                "GitHub stars:",
                details["github_stars"]
            )

        elif result["status"] == "not_found":

            not_found += 1

            print(
                "No Papers with Code record."
            )

        else:

            errors += 1

            print(
                "Lookup failed. Can retry later."
            )

        # Save progress periodically
        if (index + 1) % SAVE_EVERY == 0:

            save_progress(df)

            print(
                f"\nProgress saved: {index + 1}/{total}"
            )

        time.sleep(REQUEST_DELAY)

    # Final save
    save_progress(df)

    # ==================================================
    # FINAL VALIDATION AND REPORT
    # ==================================================

    result_df = pd.read_csv(OUTPUT_FILE)

    repository_counts = pd.to_numeric(
        result_df["repository_count"],
        errors="coerce"
    ).fillna(0)

    official_counts = pd.to_numeric(
        result_df["official_repository_count"],
        errors="coerce"
    ).fillna(0)

    status_counts = (
        result_df["paperswithcode_status"]
        .value_counts()
    )

    print("\n")

    print("=" * 65)
    print("             ENRICHMENT COMPLETED")
    print("=" * 65)

    print(
        "Total papers:",
        len(result_df)
    )

    print(
        "API records found:",
        status_counts.get("found", 0)
    )

    print(
        "Papers not found:",
        status_counts.get("not_found", 0)
    )

    print(
        "API errors:",
        status_counts.get("error", 0)
    )

    print(
        "Papers with GitHub repositories:",
        (repository_counts > 0).sum()
    )

    print(
        "Papers with official repositories:",
        (official_counts > 0).sum()
    )

    print(
        "Total linked GitHub repositories:",
        int(repository_counts.sum())
    )

    print(
        "Total official GitHub repositories:",
        int(official_counts.sum())
    )

    print("\nOutput file:")

    print(
        OUTPUT_FILE.resolve()
    )

    print("=" * 65)


if __name__ == "__main__":

    main()
