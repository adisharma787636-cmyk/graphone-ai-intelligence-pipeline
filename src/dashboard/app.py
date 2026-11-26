
import json
from pathlib import Path

import pandas as pd
import streamlit as st


# ==========================================================
# GRAPHONE AI - FUTURISTIC INTELLIGENCE DASHBOARD
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = PROJECT_ROOT / "data" / "exports"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

st.set_page_config(
    page_title="GraphOne AI | Intelligence Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==========================================================
# DATASET CONFIGURATION
# ==========================================================

DATASETS = {
    "Startups": "ai_startups.csv",
    "AI Applications": "ai_products.csv",
    "Research Papers": "arxiv_papers_enriched.csv",
    "AI Jobs": "ai_jobs_clean.csv",
    "AI News": "ai_news.csv",
    "Entity Mapping Log": "entity_mapping_log.csv",
}


# ==========================================================
# FUTURISTIC CUSTOM CSS
# ==========================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* GLOBAL */

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 10% 5%, rgba(37, 99, 235, 0.15), transparent 28%),
        radial-gradient(circle at 90% 10%, rgba(124, 58, 237, 0.13), transparent 25%),
        #080d1b !important;
    color: #e2e8f0 !important;
}

[data-testid="stAppViewContainer"] {
    background-color: #080d1b !important;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1500px;
}

/* TOP HEADER */

[data-testid="stHeader"] {
    background: rgba(8, 13, 27, 0.95) !important;
}

[data-testid="stToolbar"] {
    background: transparent !important;
}

/* GENERAL TEXT */

.stApp p,
.stApp label,
.stApp .stMarkdown,
.stApp .stMarkdown p,
.stApp .stMarkdown span {
    color: #e2e8f0;
}

.stApp h1,
.stApp h2,
.stApp h3,
.stApp h4 {
    color: #e0e7ff !important;
}

/* SIDEBAR */

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #101a30, #0a1020) !important;
    border-right: 1px solid rgba(96, 165, 250, 0.25);
}

section[data-testid="stSidebar"] * {
    color: #e2e8f0;
}

section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label {
    color: #e2e8f0 !important;
}

section[data-testid="stSidebar"] .stRadio label {
    font-weight: 500;
}

section[data-testid="stSidebar"] [role="radiogroup"] {
    gap: 8px;
}

section[data-testid="stSidebar"] [role="radiogroup"] label {
    background: rgba(30, 41, 70, 0.45);
    padding: 9px 12px;
    border-radius: 9px;
    border: 1px solid transparent;
}

section[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: rgba(59, 130, 246, 0.15);
    border-color: rgba(96, 165, 250, 0.3);
}

/* HERO SECTION */

.hero {
    padding: 35px;
    border-radius: 22px;
    background: linear-gradient(
        120deg,
        rgba(30, 64, 175, 0.28),
        rgba(109, 40, 217, 0.22),
        rgba(15, 23, 42, 0.85)
    );
    border: 1px solid rgba(96, 165, 250, 0.25);
    margin-bottom: 28px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.25);
}

.hero-title {
    font-size: 38px;
    font-weight: 800;
    letter-spacing: -1.5px;
    background: linear-gradient(90deg, #60a5fa, #a78bfa, #c4b5fd);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    color: #cbd5e1 !important;
    font-size: 15px;
    margin-top: 10px;
    line-height: 1.7;
}

/* SECTION HEADINGS */

.section-title {
    font-size: 25px;
    font-weight: 750;
    color: #e0e7ff !important;
    margin-bottom: 5px;
}

.section-description {
    color: #a5b4fc !important;
    font-size: 13px;
    margin-bottom: 22px;
}

/* METRIC CARDS */

.metric-card {
    background: linear-gradient(
        145deg,
        rgba(30, 41, 70, 0.95),
        rgba(15, 23, 42, 0.95)
    );
    border: 1px solid rgba(96, 165, 250, 0.25);
    border-radius: 17px;
    padding: 21px;
    min-height: 125px;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.18);
    transition: 0.25s ease;
}

.metric-card:hover {
    border-color: rgba(129, 140, 248, 0.7);
    transform: translateY(-3px);
}

.metric-label {
    color: #a5b4fc !important;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.metric-value {
    color: #ffffff !important;
    font-size: 29px;
    font-weight: 800;
    margin-top: 12px;
}

/* INFORMATION PANELS */

.info-card {
    background: rgba(17, 27, 49, 0.95);
    border: 1px solid rgba(96, 165, 250, 0.25);
    border-radius: 15px;
    padding: 20px;
    margin-bottom: 14px;
}

.info-card h4 {
    color: #93c5fd !important;
    margin-top: 0;
    font-size: 17px;
    font-weight: 700;
}

.info-card p {
    color: #cbd5e1 !important;
    font-size: 13px;
    line-height: 1.6;
}

/* STREAMLIT METRICS */

[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] p {
    color: #a5b4fc !important;
}

[data-testid="stMetricValue"],
[data-testid="stMetricValue"] div {
    color: #ffffff !important;
}

/* SEARCH INPUTS */

[data-testid="stTextInput"] label {
    color: #cbd5e1 !important;
}

[data-testid="stTextInput"] input {
    background-color: #111c32 !important;
    color: #ffffff !important;
    border: 1px solid #64748b !important;
    border-radius: 9px;
    caret-color: #60a5fa;
}

[data-testid="stTextInput"] input::placeholder {
    color: #94a3b8 !important;
    opacity: 1;
}

[data-testid="stTextInput"] input:focus {
    border-color: #60a5fa !important;
    box-shadow: 0 0 0 1px #60a5fa;
}

/* SELECT BOX */

.stSelectbox label {
    color: #cbd5e1 !important;
}

.stSelectbox div[data-baseweb="select"] {
    background-color: #111c32 !important;
}

/* CAPTIONS */

[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p {
    color: #a5b4fc !important;
}

/* BUTTONS */

.stButton button,
.stDownloadButton button {
    background: linear-gradient(90deg, #2563eb, #7c3aed) !important;
    color: #ffffff !important;
    border: none;
    border-radius: 9px;
    font-weight: 600;
    transition: 0.2s ease;
}

.stButton button:hover,
.stDownloadButton button:hover {
    border: 1px solid #93c5fd !important;
    color: #ffffff !important;
}

/* EXPANDERS */

[data-testid="stExpander"] {
    background: rgba(15, 23, 42, 0.8);
    border: 1px solid rgba(96, 165, 250, 0.2);
    border-radius: 10px;
}

[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p {
    color: #e0e7ff !important;
}

/* DATA TABLE */

[data-testid="stDataFrame"] {
    border: 1px solid rgba(96, 165, 250, 0.2);
    border-radius: 12px;
    overflow: hidden;
}

/* ALERTS */

[data-testid="stAlert"] {
    border-radius: 10px;
}

/* FOOTER */

.footer {
    text-align: center;
    color: #94a3b8 !important;
    font-size: 12px;
    padding: 25px 0 5px 0;
    border-top: 1px solid rgba(96, 165, 250, 0.15);
    margin-top: 40px;
}

</style>
""", unsafe_allow_html=True)


# ==========================================================
# DATA LOADING FUNCTIONS
# ==========================================================

@st.cache_data
def load_csv(file_path):

    path = EXPORT_DIR / file_path

    if not path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(path).fillna("")

    except Exception as error:
        st.warning(f"Could not load {file_path}: {error}")
        return pd.DataFrame()


@st.cache_data
def load_json(file_path):

    path = PROCESSED_DIR / file_path

    if not path.exists():
        return []

    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    except Exception as error:
        st.warning(f"Could not load {file_path}: {error}")
        return []


# ==========================================================
# LOAD DATASETS
# ==========================================================

data = {
    name: load_csv(filename)
    for name, filename in DATASETS.items()
}

llm_results = load_json("llm_extractions.json")
resolved_entities = load_json("resolved_entities.json")


# ==========================================================
# HELPER FUNCTIONS
# ==========================================================

def metric_card(label, value):

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value:,}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title, description):

    st.markdown(
        f"""
        <div class="section-title">{title}</div>
        <div class="section-description">{description}</div>
        """,
        unsafe_allow_html=True,
    )


def get_entity_count(results):

    if isinstance(results, (list, dict)):
        return len(results)

    return 0


def show_dataset(name, dataframe):

    section_header(
        name,
        f"Explore and analyze the {name.lower()} dataset collected by GraphOne AI."
    )

    if dataframe.empty:

        st.warning(
            f"No data available for {name}. "
            "Check whether the corresponding CSV file exists."
        )
        return

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Records", f"{len(dataframe):,}")

    with col2:
        st.metric("Total Columns", len(dataframe.columns))

    search = st.text_input(
        f"Search {name}",
        placeholder="Type a keyword to search the dataset...",
        key=f"search_{name}",
    )

    filtered = dataframe.copy()

    if search.strip():

        mask = filtered.astype(str).apply(
            lambda column: column.str.contains(
                search,
                case=False,
                na=False,
                regex=False,
            )
        ).any(axis=1)

        filtered = filtered[mask]

    st.caption(
        f"Showing {len(filtered):,} of {len(dataframe):,} records"
    )

    st.dataframe(
        filtered,
        use_container_width=True,
        height=480,
        hide_index=True,
    )

    st.download_button(
        label=f"⬇ Download {name} CSV",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name=f"{name.lower().replace(' ', '_')}.csv",
        mime="text/csv",
        key=f"download_{name}",
    )


# ==========================================================
# SIDEBAR NAVIGATION
# ==========================================================

with st.sidebar:

    st.markdown("""
    <div style="padding: 15px 5px 25px 5px;">
        <div style="font-size: 27px; font-weight: 800;
                    color: #93c5fd;">
            🤖 GraphOne AI
        </div>
        <div style="font-size: 11px; color: #818cf8;
                    letter-spacing: 2px;">
            INTELLIGENCE PLATFORM
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("### NAVIGATION")

    page = st.radio(
        "Select Dashboard Section",
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
        label_visibility="collapsed",
    )

    st.markdown("---")

    st.markdown("### SYSTEM STATUS")

    st.markdown("""
    <div style="
        background: #102a25;
        color: #4ade80;
        border: 1px solid #16a34a;
        border-radius: 8px;
        padding: 10px;
        font-weight: 600;
    ">
        ● Dashboard Active
    </div>
    """, unsafe_allow_html=True)

    st.caption("GraphOne AI Intelligence Pipeline")
    st.caption("Data is loaded from project files.")


# ==========================================================
# MAIN HERO HEADER
# ==========================================================

st.markdown("""
<div class="hero">

    <div class="hero-title">
        GRAPHONE AI
    </div>

    <div style="color:#c4b5fd; font-size:12px;
                font-weight:700; letter-spacing:3px;">
        AI INTELLIGENCE & DISCOVERY PLATFORM
    </div>

    <div class="hero-subtitle">
        A centralized intelligence dashboard for discovering,
        collecting, processing, and analyzing AI startups,
        applications, research papers, jobs, and industry news.
    </div>

</div>
""", unsafe_allow_html=True)


# ==========================================================
# OVERVIEW PAGE
# ==========================================================

if page == "Overview":

    section_header(
        "Intelligence Overview",
        "A complete snapshot of your AI intelligence collection pipeline."
    )

    startups = len(data["Startups"])
    applications = len(data["AI Applications"])
    papers = len(data["Research Papers"])
    jobs = len(data["AI Jobs"])
    news = len(data["AI News"])
    mappings = len(data["Entity Mapping Log"])

    metric_columns = st.columns(3)

    metrics = [
        ("AI STARTUPS", startups),
        ("AI APPLICATIONS", applications),
        ("RESEARCH PAPERS", papers),
        ("AI JOBS", jobs),
        ("AI NEWS", news),
        ("ENTITY MAPPINGS", mappings),
    ]

    for index, (label, value) in enumerate(metrics):

        with metric_columns[index % 3]:
            metric_card(label, value)

    st.markdown("")

    section_header(
        "Dataset Analytics",
        "Record distribution across the major intelligence datasets."
    )

    chart_data = pd.DataFrame({
        "Dataset": list(data.keys()),
        "Records": [len(df) for df in data.values()],
    })

    if chart_data["Records"].sum() > 0:

        st.bar_chart(
            chart_data.set_index("Dataset"),
            y="Records",
            use_container_width=True,
        )

    else:

        st.info("No dataset records are currently available.")

    section_header(
        "Dataset Summary",
        "Overview of the collected information."
    )

    summary = pd.DataFrame([
        {
            "Dataset": name,
            "Records": len(df),
            "Columns": len(df.columns),
            "Status": "Available" if not df.empty else "Missing",
        }
        for name, df in data.items()
    ])

    st.dataframe(
        summary,
        use_container_width=True,
        hide_index=True,
    )

    section_header(
        "Intelligence Pipeline",
        "How GraphOne AI collects and processes information."
    )

    pipeline_columns = st.columns(3)

    pipeline_steps = [
        (
            "01",
            "Data Collection",
            "Collect AI startups, applications, jobs, research papers, and news."
        ),
        (
            "02",
            "Data Processing",
            "Clean, organize, and structure the collected information."
        ),
        (
            "03",
            "LLM Extraction",
            "Extract useful information and entities from AI-related content."
        ),
        (
            "04",
            "Entity Resolution",
            "Identify and map entities across different information sources."
        ),
        (
            "05",
            "Data Export",
            "Store processed information in CSV and JSON formats."
        ),
        (
            "06",
            "Visualization",
            "Present the collected intelligence through this dashboard."
        ),
    ]

    for index, (number, title, description) in enumerate(pipeline_steps):

        with pipeline_columns[index % 3]:

            st.markdown(
                f"""
                <div class="info-card">

                    <div style="
                        color:#818cf8;
                        font-size:12px;
                        font-weight:800;
                    ">
                        STEP {number}
                    </div>

                    <h4 style="
                        color:#93c5fd !important;
                        font-size:17px;
                        font-weight:700;
                        margin-top:8px;
                    ">
                        {title}
                    </h4>

                    <p style="color:#cbd5e1 !important;">
                        {description}
                    </p>

                </div>
                """,
                unsafe_allow_html=True,
            )

    section_header(
        "Data Availability",
        "Check whether the required project files are available."
    )

    for name, filename in DATASETS.items():

        file_path = EXPORT_DIR / filename

        if file_path.exists():

            st.markdown(
                f"""
                <div style="
                    background: #102a25;
                    border: 1px solid #16a34a;
                    border-radius: 10px;
                    padding: 17px;
                    margin-bottom: 12px;
                    color: #bbf7d0;
                    font-weight: 600;
                ">
                    <span style="color: #4ade80;">●</span>
                    &nbsp; {name}: File available
                </div>
                """,
                unsafe_allow_html=True,
            )

        else:

            st.markdown(
                f"""
                <div style="
                    background: #301b25;
                    border: 1px solid #ef4444;
                    border-radius: 10px;
                    padding: 17px;
                    margin-bottom: 12px;
                    color: #fecaca;
                    font-weight: 600;
                ">
                    <span style="color: #f87171;">●</span>
                    &nbsp; {name}: File not found
                </div>
                """,
                unsafe_allow_html=True,
            )


# ==========================================================
# STARTUPS
# ==========================================================

elif page == "Startups":

    show_dataset("Startups", data["Startups"])


# ==========================================================
# AI APPLICATIONS
# ==========================================================

elif page == "AI Applications":

    show_dataset("AI Applications", data["AI Applications"])


# ==========================================================
# RESEARCH PAPERS
# ==========================================================

elif page == "Research Papers":

    show_dataset("Research Papers", data["Research Papers"])


# ==========================================================
# AI JOBS
# ==========================================================

elif page == "AI Jobs":

    show_dataset("AI Jobs", data["AI Jobs"])


# ==========================================================
# AI NEWS
# ==========================================================

elif page == "AI News":

    show_dataset("AI News", data["AI News"])


# ==========================================================
# LLM RESULTS
# ==========================================================

elif page == "LLM Results":

    section_header(
        "LLM Extraction Results",
        "Explore information extracted from AI-related articles using LLM processing."
    )

    total_results = get_entity_count(llm_results)

    metric_card("TOTAL EXTRACTION RECORDS", total_results)

    st.markdown("")

    if not llm_results:

        st.warning(
            "No LLM extraction results found. "
            "Check data/processed/llm_extractions.json."
        )

    elif isinstance(llm_results, list):

        for index, item in enumerate(llm_results, start=1):

            if isinstance(item, dict):

                title = (
                    item.get("title")
                    or item.get("article_title")
                    or item.get("url")
                    or f"Extraction Record {index}"
                )

                with st.expander(f"📄 {title}"):

                    st.json(item)

            else:

                with st.expander(f"Extraction Record {index}"):

                    st.write(item)

    elif isinstance(llm_results, dict):

        for title, item in llm_results.items():

            with st.expander(str(title)):

                st.json(item)


# ==========================================================
# ENTITY RESOLUTION
# ==========================================================

elif page == "Entity Resolution":

    section_header(
        "Entity Resolution",
        "Explore entity mappings and resolved records generated by the pipeline."
    )

    mapping_df = data["Entity Mapping Log"]

    col1, col2 = st.columns(2)

    with col1:

        metric_card("MAPPING RECORDS", len(mapping_df))

    with col2:

        metric_card(
            "RESOLVED ENTITY RECORDS",
            get_entity_count(resolved_entities),
        )

    st.markdown("")

    if not mapping_df.empty:

        st.markdown("### Entity Mapping Records")

        search = st.text_input(
            "Search entity mappings",
            placeholder="Search by entity name or mapping...",
            key="entity_search",
        )

        filtered = mapping_df.copy()

        if search.strip():

            mask = filtered.astype(str).apply(
                lambda column: column.str.contains(
                    search,
                    case=False,
                    na=False,
                    regex=False,
                )
            ).any(axis=1)

            filtered = filtered[mask]

        st.caption(
            f"Showing {len(filtered)} of {len(mapping_df)} records"
        )

        st.dataframe(
            filtered,
            use_container_width=True,
            height=400,
            hide_index=True,
        )

        st.download_button(
            "⬇ Download Entity Mapping CSV",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name="entity_mapping_log.csv",
            mime="text/csv",
        )

    else:

        st.warning("Entity mapping CSV file is not available.")

    if resolved_entities:

        st.markdown("### Resolved Entities")

        with st.expander("View resolved entity JSON"):

            st.json(resolved_entities)

        st.download_button(
            "⬇ Download Resolved Entities JSON",
            data=json.dumps(
                resolved_entities,
                indent=4,
                ensure_ascii=False,
            ),
            file_name="resolved_entities.json",
            mime="application/json",
        )

    else:

        st.info("No resolved entity JSON records are available.")


# ==========================================================
# FOOTER
# ==========================================================

st.markdown("""
<div class="footer">

    <div style="
        font-weight:700;
        color:#93c5fd;
        margin-bottom:5px;
    ">
        GRAPHONE AI | INTELLIGENCE PLATFORM
    </div>

    AI Intelligence Collection & Analysis Dashboard

    <br>

    Built with Python, Pandas and Streamlit

</div>
""", unsafe_allow_html=True)
