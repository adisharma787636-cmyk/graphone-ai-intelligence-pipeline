
import json
import time
import xml.etree.ElementTree as ET

import requests


# STEP 1: Fetch one batch of research papers from arXiv
def fetch_arxiv_papers(start=0, max_results=100):

    url = "https://export.arxiv.org/api/query"

    params = {
        "search_query": "cat:cs.AI",
        "start": start,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }

    response = requests.get(
        url,
        params=params,
        timeout=60
    )

    response.raise_for_status()

    return response.text


# STEP 2: Extract complete paper information from XML
def extract_papers(xml_data):

    root = ET.fromstring(xml_data)

    namespace = {
        "atom": "http://www.w3.org/2005/Atom"
    }

    entries = root.findall("atom:entry", namespace)

    papers = []

    for entry in entries:

        # Extract title
        title_element = entry.find("atom:title", namespace)
        title = (
            title_element.text.strip()
            if title_element is not None and title_element.text
            else None
        )

        # Extract abstract
        summary_element = entry.find("atom:summary", namespace)
        abstract = (
            summary_element.text.strip()
            if summary_element is not None and summary_element.text
            else None
        )

        # Extract authors
        authors = []

        for author in entry.findall("atom:author", namespace):

            name_element = author.find("atom:name", namespace)

            if name_element is not None and name_element.text:
                authors.append(name_element.text.strip())

        # Extract publication date
        published_element = entry.find("atom:published", namespace)
        published = (
            published_element.text
            if published_element is not None
            else None
        )

        # Extract updated date
        updated_element = entry.find("atom:updated", namespace)
        updated = (
            updated_element.text
            if updated_element is not None
            else None
        )

        # Extract paper URL
        paper_id_element = entry.find("atom:id", namespace)

        paper_url = (
            paper_id_element.text.strip()
            if paper_id_element is not None and paper_id_element.text
            else None
        )

        # Extract arXiv ID
        arxiv_id = (
            paper_url.rstrip("/").split("/")[-1]
            if paper_url
            else None
        )

        # Create paper dictionary
        paper = {
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "published": published,
            "updated": updated,
            "paper_url": paper_url,
            "arxiv_id": arxiv_id
        }

        papers.append(paper)

    return papers


# STEP 3: Fetch up to 1,000 papers using pagination
def fetch_all_arxiv_papers(total_papers=1000, batch_size=100):

    all_papers = []

    seen_ids = set()

    total_batches = (total_papers + batch_size - 1) // batch_size

    print(f"\nTarget papers: {total_papers}")
    print(f"Batch size: {batch_size}")
    print(f"Total batches: {total_batches}")

    for batch_number in range(total_batches):

        start = batch_number * batch_size

        current_batch_size = min(
            batch_size,
            total_papers - len(all_papers)
        )

        print(
            f"\nFetching batch {batch_number + 1}/{total_batches} "
            f"(starting position: {start})..."
        )

        try:

            xml_data = fetch_arxiv_papers(
                start=start,
                max_results=current_batch_size
            )

            batch_papers = extract_papers(xml_data)

            new_papers = 0

            for paper in batch_papers:

                arxiv_id = paper["arxiv_id"]

                if arxiv_id and arxiv_id not in seen_ids:

                    seen_ids.add(arxiv_id)
                    all_papers.append(paper)
                    new_papers += 1

            print("Papers received:", len(batch_papers))
            print("New unique papers:", new_papers)
            print("Total unique papers collected:", len(all_papers))

            if len(batch_papers) < current_batch_size:
                print("\nNo more papers returned by arXiv.")
                break

        except requests.RequestException as error:

            print("\nNetwork/API error:", error)
            print("Stopping collection to preserve collected records.")
            break

        except ET.ParseError as error:

            print("\nXML parsing error:", error)
            print("Stopping collection to preserve collected records.")
            break

        # Wait between requests to respect arXiv API usage
        if batch_number < total_batches - 1:
            time.sleep(3)

    return all_papers


# STEP 4: Save research papers into a JSON file
def save_papers_to_json(papers):

    file_path = "data/raw/arxiv_papers.json"

    with open(file_path, "w", encoding="utf-8") as file:

        json.dump(
            papers,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("\nResearch papers saved successfully!")
    print("File location:", file_path)


# STEP 5: Main program
if __name__ == "__main__":

    print("Connecting to arXiv API...")

    try:

        papers = fetch_all_arxiv_papers(
            total_papers=1000,
            batch_size=100
        )

        print("\nCollection completed!")

        save_papers_to_json(papers)

        print("\nResearch Paper Collection Summary")
        print("=" * 45)

        for number, paper in enumerate(papers[:5], start=1):

            print(f"\nPaper {number}")
            print("Title:", paper["title"])
            print("Authors:", paper["authors"])
            print("Published:", paper["published"])
            print("Updated:", paper["updated"])
            print("arXiv ID:", paper["arxiv_id"])
            print("Paper URL:", paper["paper_url"])

        print("\nTotal unique papers extracted:", len(papers))

        if len(papers) < 1000:
            print("Note: Fewer than 1,000 papers were collected.")

    except requests.RequestException as error:

        print("\nCould not connect to arXiv API:", error)
