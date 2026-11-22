
import json
from pathlib import Path

import pandas as pd
import streamlit as st


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = PROJECT_ROOT / "data" / "exports"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

st.set_page_config(
    page_title="GraphOne AI Pipeline",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------
# DATA LOADING
# --------------------------------------------------

DATASETS = {
    "Startups": "ai_startups.csv",
    "AI Applications": "ai_products.csv",
    "Research Papers": "arxiv_papers.csv",
    "AI Jobs": "ai_jobs.csv",
    "AI News": "ai_news.csv",
    "Entity Mapping Log": "entity_mapping_log.csv",
}


@st.cache_data
def load_csv(filename):
    path = EXPORT_DIR / filename

    if not path.exists():
        return pd.DataFrame()

    return pd.read_csv(path).fillna("")


@st.cache_data
def load_json(filename):
    path = PROCESSED_DIR / filename

    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


data = {
    name: load_csv(filename)
    for name, filename in DATASETS.items()
}

llm_results = load_json("llm_extractions.json")


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("🤖 GraphOne AI Pipeline")
st.markdown(
    """
    ### AI Intelligence Collection & Processing Platform

    Collecting, analyzing, extracting and organizing
    information from the Artificial Intelligence ecosystem.
    """
)

st.divider()


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Select a section",
    [
        "Overview",
        "Startups",
        "AI Applications",
        "Research Papers",
        "AI Jobs",
        "AI News",
        "LLM Results",
        "Entity Resolution",
    ],
)

st.sidebar.divider()

st.sidebar.success("Pipeline data loaded")

st.sidebar.caption(
    "GraphOne AI Engineer Assignment"
)


# --------------------------------------------------
# OVERVIEW
# --------------------------------------------------

if page == "Overview":

    st.subheader("Pipeline Overview")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "AI Startups",
        f"{len(data['Startups']):,}"
    )

    c2.metric(
        "AI Applications",
        f"{len(data['AI Applications']):,}"
    )

    c3.metric(
        "Research Papers",
        f"{len(data['Research Papers']):,}"
    )

    c4, c5, c6 = st.columns(3)

    c4.metric(
        "Fresh AI Jobs",
        f"{len(data['AI Jobs']):,}"
    )

    c5.metric(
        "Fresh AI News",
        f"{len(data['AI News']):,}"
    )

    c6.metric(
        "Entity Mapping Records",
        f"{len(data['Entity Mapping Log']):,}"
    )

    st.divider()

    st.subheader("How the Pipeline Works")

    steps = [
        ("01", "Data Collection", "Collect AI startups, applications, research papers, jobs and news."),
        ("02", "Data Processing", "Clean, normalize and organize collected information."),
        ("03", "LLM Extraction", "Use Gemini and Groq fallback to identify AI entities."),
        ("04", "Entity Resolution", "Identify duplicate names and organize canonical entities."),
        ("05", "Data Export", "Store structured results in JSON and CSV files."),
    ]

    for number, title, description in steps:
        with st.container(border=True):
            st.markdown(f"**{number} · {title}**")
            st.write(description)

    st.divider()

    st.subheader("Dataset Summary")

    summary = pd.DataFrame([
        {
            "Dataset": name,
            "Records": len(frame),
            "Status": "Available" if not frame.empty else "Missing",
        }
        for name, frame in data.items()
    ])

    st.dataframe(
        summary,
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Counts reflect the CSV files currently available in the project."
    )


# --------------------------------------------------
# GENERIC DATASET VIEW
# --------------------------------------------------

elif page in DATASETS:

    df = data[page]

    st.subheader(page)
    st.write(f"Total records: **{len(df):,}**")

    if df.empty:
        st.warning("No records found for this dataset.")
    else:

        search = st.text_input(
            f"Search {page}",
            placeholder="Enter a name, keyword or company..."
        )

        filtered = df

        if search:
            mask = df.astype(str).apply(
                lambda column: column.str.contains(
                    search,
                    case=False,
                    regex=False
                )
            ).any(axis=1)

            filtered = df[mask]

        st.write(f"Showing {len(filtered):,} matching records")

        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "Download this dataset as CSV",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name=f"{page.lower().replace(' ', '_')}.csv",
            mime="text/csv",
        )


# --------------------------------------------------
# LLM RESULTS
# --------------------------------------------------

elif page == "LLM Results":

    st.subheader("Large Language Model Results")

    st.write(
        "The LLM pipeline analyzes collected AI news articles "
        "and extracts structured entities."
    )

    st.metric(
        "Total Extracted Entities",
        sum(
            len(item.get("entities", []))
            for item in llm_results
            if isinstance(item, dict)
        )
    )

    if not llm_results:
        st.warning("LLM output file not found or empty.")
    else:

        for index, article in enumerate(llm_results, 1):

            with st.expander(
                f"Article {index}: "
                + str(article.get("article_title", article.get("title", "Untitled")))
            ):

                st.json(article)


# --------------------------------------------------
# ENTITY RESOLUTION
# --------------------------------------------------

elif page == "Entity Resolution":

    st.subheader("Entity Resolution")

    df = data["Entity Mapping Log"]

    if df.empty:
        st.warning("Entity mapping data not found.")
    else:

        st.metric(
            "Total Mapping Records",
            len(df)
        )

        st.write(
            "This module organizes extracted names and records "
            "their matching or review status."
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "GraphOne AI Pipeline | AI Data Collection, "
    "LLM Extraction & Entity Resolution"
)
