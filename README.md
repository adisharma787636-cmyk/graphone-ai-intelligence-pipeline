# GraphOne AI — Intelligence Pipeline

> An AI-powered data intelligence pipeline for collecting, processing, extracting, and resolving information across the artificial intelligence ecosystem.

## Overview

GraphOne AI is a Python-based data intelligence project designed to collect and organize information about AI startups, public AI applications, research papers, job opportunities, and AI news.

The pipeline combines data collection, data processing, Large Language Model (LLM) extraction, and entity resolution to transform information from multiple sources into structured datasets.

It also includes an interactive Streamlit dashboard for exploring collected information and processing results.

## Key Features

- **AI Startup Collection:** Collects and processes AI startup information.
- **AI Application Discovery:** Collects public AI applications from Hugging Face Spaces.
- **Research Paper Collection:** Retrieves AI research papers using the arXiv API.
- **GitHub Repository Enrichment:** Enriches eligible research paper records with repository information.
- **AI Job Collection:** Collects AI-related job listings from multiple job platforms.
- **AI News Collection:** Collects recent AI news and article content.
- **LLM-Based Extraction:** Extracts structured entities from article content using language models.
- **Provider Fallback:** Supports a Gemini-to-Groq fallback workflow, with optional DeepSeek integration.
- **Reliable Processing:** Includes retry handling, rate-limit handling, and semantic chunking for large inputs.
- **Entity Resolution:** Uses name normalization, aliases, and fuzzy matching to identify similar entities.
- **Interactive Dashboard:** Provides a Streamlit interface to explore collected data and processing results.

## Technology Stack

| Area | Technologies |
|---|---|
| Programming language | Python |
| Data collection | Requests, aiohttp, BeautifulSoup |
| AI and LLM | Google Gemini, Groq |
| Research data | arXiv API, Papers with Code API |
| AI applications | Hugging Face API |
| Entity resolution | RapidFuzz |
| Data processing | Pandas, JSON, CSV |
| Dashboard | Streamlit |
| Configuration | Environment variables |

## Project Results

The following figures represent recorded project runs and should be interpreted in the context of their respective sources.

| Dataset or component | Recorded result |
|---|---:|
| AI startups | 3,926 unique records |
| Public AI applications | 1,014 records |
| AI research papers | 1,000 records |
| AI-related fresh jobs | 36 records |
| Fresh AI news articles | 4 articles |
| LLM-extracted entities | 35 source mappings |
| Resolved entities | 34 unique entities |

### Data Sources

- Labspie startup dataset
- Hugging Face public Spaces API
- arXiv API
- Papers with Code API
- Remote OK
- Jobicy
- Arbeitnow
- We Work Remotely
- OpenAI, Google DeepMind, Hugging Face, TechCrunch AI and MIT Technology Review news sources

**Data collection note:** Results depend on source availability, API responses, relevance filters, and collection time. The latest recorded news run returned four fresh articles, all from TechCrunch AI. Not every configured source necessarily contributes records in every run.

## System Workflow

1. Collect information from configured public sources and APIs.
2. Store and process the collected records.
3. Clean and enrich relevant datasets.
4. Extract entities from news content using LLM services.
5. Apply provider fallback and reliability handling when required.
6. Resolve entity names using normalization, aliases, and fuzzy matching.
7. Export structured results for analysis.
8. Explore the results using the Streamlit dashboard.

## Project Structure

```text
graphone-ai-intelligence-pipeline/
│
├── .gitignore
├── requirements.txt
├── settings.json
├── README.md
│
└── src/
    ├── dashboard/
    │   └── app.py
    │
    ├── processors/
    │   ├── clean_jobs_csv.py
    │   ├── enrich_arxiv_github.py
    │   └── llm_processor.py
    │
    ├── resolver/
    │   ├── entity_resolver.py
    │   └── entity_resolver_backup.py
    │
    ├── scrapers/
    │   ├── ai_products_collector.py
    │   ├── arxiv_collector.py
    │   ├── job_collector.py
    │   ├── news_collector.py
    │   └── startup_collector.py
    │
    ├── services/
    │   ├── extraction_schema.py
    │   ├── gemini_service.py
    │   ├── groq_service.py
    │   ├── llm_manager.py
    │   ├── test_llm_reliability.py
    │   └── test_provider_fallback.py
    │
    ├── main.py
    └── test_papers_api.py
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/adisharma787636-cmyk/graphone-ai-intelligence-pipeline.git
```

### 2. Open the project folder

```bash
cd graphone-ai-intelligence-pipeline
```

### 3. Create a virtual environment

```bash
python -m venv .venv
```

### 4. Activate the virtual environment

**Windows PowerShell:**

```powershell
.venv\Scripts\Activate.ps1
```

**Git Bash:**

```bash
source .venv/Scripts/activate
```

### 5. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 6. Configure API credentials

Some services require API credentials.

Create a local `.env` file in the project root and configure the credentials required by the services you want to use.

Never commit `.env` files, API keys, or other private credentials to GitHub.

## Running the Project

### Launch the Streamlit dashboard

```bash
python -m streamlit run src/dashboard/app.py
```

The dashboard can be opened using the local URL displayed in the terminal.

### Run individual data collectors

```bash
python -m src.scrapers.startup_collector
```

```bash
python -m src.scrapers.ai_products_collector
```

```bash
python -m src.scrapers.arxiv_collector
```

```bash
python -m src.scrapers.job_collector
```

```bash
python -m src.scrapers.news_collector
```

### Run processing components

```bash
python -m src.processors.llm_processor
```

```bash
python -m src.resolver.entity_resolver
```

The commands above run individual pipeline components. Configure the required credentials and dependencies before running services that use external APIs.

## Reliability and Entity Resolution

GraphOne AI includes reliability mechanisms for LLM-based processing:

- Retry handling for rate-limit responses.
- Exponential backoff with jitter.
- Semantic chunking for oversized inputs.
- Provider fallback when a configured service fails.
- Entity normalization and alias matching.
- Fuzzy matching with review thresholds.
- Entity mapping logs for traceability.

Reliability tests include simulated failure scenarios. These tests demonstrate the handling logic and do not imply that every external provider failure has been tested in production.

## Current Scope and Limitations

- The collected datasets are not included in this repository because generated data folders are excluded by `.gitignore`.
- Some source records may require manual verification.
- AI application records represent public Hugging Face Spaces, not necessarily commercial products.
- Research paper collection currently uses the `cs.AI` arXiv category.
- GitHub enrichment depends on the availability of matching records from Papers with Code.
- DeepSeek integration is optional and was not configured in the latest recorded live test.
- The latest news collection run returned four fresh articles from one source.

## Future Improvements

- Expand research collection across additional AI-related categories.
- Improve source coverage and data validation.
- Add more LLM providers and provider monitoring.
- Improve entity classification and manual review workflows.
- Add automated pipeline scheduling.
- Improve dashboard analytics and visual reporting.
- Add automated tests for the complete end-to-end pipeline.

## Author

**Aditya Sharma**

MCA — Artificial Intelligence and Machine Learning

GitHub: [@adisharma787636-cmyk](https://github.com/adisharma787636-cmyk)

Project: [GraphOne AI Intelligence Pipeline](https://github.com/adisharma787636-cmyk/graphone-ai-intelligence-pipeline)

---

*GraphOne AI is an educational and portfolio project demonstrating data engineering, AI integration, LLM-based information extraction, and entity resolution.*