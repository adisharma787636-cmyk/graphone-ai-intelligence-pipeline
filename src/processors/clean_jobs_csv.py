
import re
import html
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup


INPUT_FILE = Path("data/exports/ai_jobs.csv")
OUTPUT_FILE = Path("data/exports/ai_jobs_clean.csv")


def clean_html_description(value):

    if pd.isna(value):
        return ""

    text = str(value)

    # Decode escaped HTML entities repeatedly
    for _ in range(3):
        decoded = html.unescape(text)
        if decoded == text:
            break
        text = decoded

    # Parse the decoded HTML
    soup = BeautifulSoup(text, "html.parser")

    # Preserve bullet points
    for li in soup.find_all("li"):
        li.insert_before("\n• ")
        li.append("\n")

    # Extract readable text
    text = soup.get_text(separator=" ", strip=True)

    # Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def main():

    print("Reading original jobs CSV...")

    df = pd.read_csv(INPUT_FILE)

    print("Original records:", len(df))

    df["description"] = df["description"].apply(
        clean_html_description
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    # Verify saved file
    check = pd.read_csv(OUTPUT_FILE)

    remaining_tags = check["description"].str.contains(
        r"<\s*/?\s*[a-zA-Z][^>]*>",
        regex=True,
        na=False
    ).sum()

    print("\n================================")
    print("CLEANING COMPLETED")
    print("================================")
    print("Records:", len(check))
    print("Columns:", len(check.columns))
    print("Remaining HTML tags:", remaining_tags)
    print("Output:", OUTPUT_FILE.resolve())

    print("\nJOB 8 PREVIEW:")
    print(check.loc[7, "description"][:1500])


if __name__ == "__main__":
    main()
