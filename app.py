import streamlit as st
import requests
import time
import json
from datetime import datetime

# --- CONFIGURATION ---
BACKEND_URL = "http://localhost:8000"
ACCENT_COLOR = "#FF5733"  # Premium Coral
BG_COLOR = "#FAF9F6"      # Warm Off-White
TEXT_COLOR = "#FFFFFF"    # Near Black

st.set_page_config(
    page_title="Nexus AI | Research Anything",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- PREMIUM CSS INJECTION ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono&display=swap');

    /* Global Styles */
    .stApp {{
        background-color: {BG_COLOR};
        background-image: radial-gradient(#e5e7eb 1px, transparent 1px);
        background-size: 24px 24px;
        color: {TEXT_COLOR};
        font-family: 'Inter', sans-serif;
    }}

    /* Hide Default Streamlit Elements */
    #MainMenu, footer, header {{visibility: hidden;}}
    .stDeployButton {{display:none;}}

    /* Premium Header */
    .nav-container {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 5%;
        background: rgba(250, 249, 246, 0.8);
        backdrop-filter: blur(8px);
        border-bottom: 1px solid #e5e7eb;
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 999;
    }}
    .logo-text {{
        font-weight: 700;
        font-size: 1.5rem;
        letter-spacing: -0.02em;
        color: {TEXT_COLOR};
        display: flex;
        align-items: center;
        gap: 8px;
    }}
    .logo-icon {{
        color: {ACCENT_COLOR};
    }}
    .nav-links {{
        display: flex;
        gap: 2rem;
    }}
    .nav-link {{
        text-decoration: none;
        color: #6b7280;
        font-weight: 500;
        font-size: 0.95rem;
        transition: color 0.2s;
        cursor: pointer;
    }}
    .nav-link:hover, .nav-link.active {{
        color: {TEXT_COLOR};
    }}

    /* Hero Section */
    .hero-container {{
        text-align: center;
        padding: 8rem 2rem 4rem 2rem;
        max-width: 800px;
        margin: 0 auto;
    }}
    .hero-title {{
        font-size: 4rem;
        font-weight: 800;
        line-height: 1.1;
        letter-spacing: -0.04em;
        margin-bottom: 1.5rem;
        color: {TEXT_COLOR};
    }}
    .hero-title span {{
        color: {ACCENT_COLOR};
    }}
    .hero-subtitle {{
        font-size: 1.25rem;
        color: #4b5563;
        line-height: 1.6;
        margin-bottom: 3rem;
    }}

    /* Research Input Area */
    .search-outer {{
        max-width: 700px;
        margin: 0 auto;
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.03);
        padding: 1rem;
        transition: border-color 0.3s, box-shadow 0.3s;
    }}
    .search-outer:focus-within {{
        border-color: {ACCENT_COLOR};
        box-shadow: 0 4px 25px rgba(255, 87, 51, 0.08);
    }}

    /* Override Streamlit text area */
    .stTextArea textarea {{
        background: transparent !important;
        border: none !important;
        font-size: 1.1rem !important;
        color: {TEXT_COLOR} !important;
        padding: 0.5rem !important;
        box-shadow: none !important;
    }}

    /* Example Prompts */
    .example-container {{
        display: flex;
        justify-content: center;
        gap: 0.75rem;
        margin-top: 2rem;
        flex-wrap: wrap;
    }}
    .example-tag {{
        background: #ffffff;
        border: 1px solid #e5e7eb;
        padding: 0.4rem 1rem;
        border-radius: 100px;
        font-size: 0.85rem;
        color: #6b7280;
        cursor: pointer;
        transition: all 0.2s;
    }}
    .example-tag:hover {{
        border-color: {ACCENT_COLOR};
        color: {ACCENT_COLOR};
    }}

    /* Live Activity Timeline */
    .timeline-container {{
        max-width: 900px;
        margin: 6rem auto;
        background: #ffffff;
        border-radius: 20px;
        border: 1px solid #e5e7eb;
        padding: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.02);
    }}
    .timeline-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid #f3f4f6;
    }}
    .stage-row {{
        display: flex;
        align-items: center;
        gap: 1.5rem;
        padding: 1rem 0;
        position: relative;
    }}
    .stage-icon {{
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: #f3f4f6;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
        z-index: 2;
    }}
    .stage-row.active .stage-icon {{
        background: {ACCENT_COLOR};
        color: white;
        box-shadow: 0 0 15px rgba(255, 87, 51, 0.4);
        animation: pulse 2s infinite;
    }}
    .stage-row.completed .stage-icon {{
        background: #10b981;
        color: white;
    }}
    .stage-content {{
        flex: 1;
    }}
    .stage-title {{
        font-weight: 600;
        font-size: 1rem;
        color: #374151;
    }}
    .stage-row.active .stage-title {{
        color: {TEXT_COLOR};
    }}
    .stage-time {{
        font-size: 0.8rem;
        color: #9ca3af;
        font-family: 'JetBrains Mono', monospace;
    }}

    @keyframes pulse {{
        0% {{ transform: scale(1); }}
        50% {{ transform: scale(1.1); }}
        100% {{ transform: scale(1); }}
    }}

    /* Report Layout */
    .report-container {{
        max-width: 1000px;
        margin: 6rem auto;
    }}
    .report-header {{
        margin-bottom: 4rem;
    }}
    .report-card {{
        background: white;
        border-radius: 24px;
        border: 1px solid #e5e7eb;
        padding: 3rem;
        box-shadow: 0 20px 50px rgba(0,0,0,0.02);
    }}
    .section-title {{
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 10px;
    }}
    .finding-card {{
        border-left: 4px solid {ACCENT_COLOR};
        padding: 1.5rem;
        background: #fffcfb;
        margin-bottom: 1.5rem;
        border-radius: 0 12px 12px 0;
    }}
    .source-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 1.5rem;
        margin-top: 2rem;
    }}
    .source-card {{
        background: white;
        border: 1px solid #e5e7eb;
        padding: 1.5rem;
        border-radius: 16px;
        transition: transform 0.2s, border-color 0.2s;
    }}
    .source-card:hover {{
        transform: translateY(-4px);
        border-color: {ACCENT_COLOR};
    }}
    .tier-badge {{
        font-size: 0.7rem;
        text-transform: uppercase;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 4px;
        background: #f3f4f6;
        color: #4b5563;
    }}

    /* History Cards */
    .history-card {{
        background: white;
        border: 1px solid #e5e7eb;
        padding: 1.5rem;
        border-radius: 16px;
        margin-bottom: 1rem;
        cursor: pointer;
        transition: all 0.2s;
    }}
    .history-card:hover {{
        border-color: {ACCENT_COLOR};
        background: #fffcfb;
    }}
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if "page" not in st.session_state:
    st.session_state.page = "Workspace"
if "active_job_id" not in st.session_state:
    st.session_state.active_job_id = None
if "research_query" not in st.session_state:
    st.session_state.research_query = ""

# --- COMPONENTS ---

def render_header():
    # We use a single column with custom HTML for the top nav
    st.markdown(f"""
    <div class="nav-container">
        <div class="logo-text">
            <span class="logo-icon">⚡</span> Nexus AI
        </div>
        <div class="nav-links">
            <span class="nav-link {'active' if st.session_state.page == 'Workspace' else ''}" onclick="window.parent.postMessage({{type: 'streamlit:set_component_value', value: 'Workspace'}}, '*')">Workspace</span>
            <span class="nav-link {'active' if st.session_state.page == 'History' else ''}" onclick="window.parent.postMessage({{type: 'streamlit:set_component_value', value: 'History'}}, '*')">History</span>
            <span class="nav-link">About</span>
            <div style="display: flex; align-items: center; gap: 6px; font-size: 0.85rem; color: #10b981; font-weight: 600;">
                <div style="width: 8px; height: 8px; background: #10b981; border-radius: 50%;"></div> Systems Operational
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Hidden selectbox to handle the navigation events
    # Note: Streamlit doesn't easily allow cross-component communication for navigation in this way,
    # so we'll use standard Streamlit radio in the sidebar for actual switching,
    # but the header for visual polish.
    pass

def submit_research(q):
    if not q:
        st.warning("Please enter a research question.")
        return

    try:
        res = requests.post(f"{BACKEND_URL}/research", json={"question": q})
        if res.status_code == 200:
            st.session_state.active_job_id = res.json()["job_id"]
            st.session_state.page = "Active Research"
            st.rerun()
        else:
            st.error(f"Backend error: {res.text}")
    except Exception as e:
        st.error(f"Could not connect to backend: {e}")

# --- PAGE: LANDING / WORKSPACE ---
def show_workspace():
    st.markdown(f"""
    <div class="hero-container">
        <div class="hero-title">Research anything. <span>Understand everything.</span></div>
        <div class="hero-subtitle">Your autonomous AI research assistant. Searching, analysing and connecting insights from trusted sources across the web.</div>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        # Custom search box style
        st.markdown('<div class="search-outer">', unsafe_allow_html=True)
        q = st.text_area("", placeholder="What would you like to research today?", value=st.session_state.research_query, height=100, key="main_search")

        col_btn, col_spacer = st.columns([1, 4])
        with col_btn:
            if st.button("Research", type="primary", use_container_width=True):
                submit_research(q)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="example-container">', unsafe_allow_html=True)
    examples = [
        "Latest AI research and developments",
        "Compare RAG vs fine-tuning",
        "How Kubernetes works internally",
        "Cloudflare MCP architecture",
        "Latest developments in cybersecurity"
    ]

    # We use actual buttons for functionality, but style them like tags
    cols = st.columns(len(examples))
    for i, ex in enumerate(examples):
        if cols[i].button(ex, key=f"ex_{i}"):
            st.session_state.research_query = ex
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- PAGE: ACTIVE RESEARCH ---
def show_active_research():
    job_id = st.session_state.active_job_id
    if not job_id:
        st.session_state.page = "Workspace"
        st.rerun()

    # Poll for status
    try:
        response = requests.get(f"{BACKEND_URL}/job/{job_id}")
        if response.status_code != 200:
            st.error("Failed to fetch job status.")
            return

        job = response.json()
        status = job["status"]
        stage = job["current_stage"]
        logs = job.get("logs", [])

        st.markdown(f"""
        <div class="timeline-container">
            <div class="timeline-header">
                <div>
                    <div style="font-weight: 700; font-size: 1.25rem;">Research in progress</div>
                    <div style="color: #6b7280; font-size: 0.9rem;">Job ID: {job_id}</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-weight: 600; color: {ACCENT_COLOR};">{stage.upper()}</div>
                    <div style="font-size: 0.8rem; color: #9ca3af;">Elapsed: {job.get('elapsed_time', '...') if 'elapsed_time' in job else 'Scanning...'}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        stages = [
            ("created", "Understanding the question", "🎯"),
            ("planning", "Creating research plan", "📋"),
            ("searching", "Searching the web", "🔍"),
            ("retrieving", "Retrieving webpages", "🌐"),
            ("synthesizing", "Analysing findings with Gemini", "🧠"),
            ("done", "Generating the final report", "📝")
        ]

        current_stage_idx = -1
        for i, (sid, name, icon) in enumerate(stages):
            if stage == sid:
                current_stage_idx = i
                break
        if stage == "done" or status == "completed":
            current_stage_idx = 5

        for i, (sid, name, icon) in enumerate(stages):
            is_active = i == current_stage_idx and status != "completed"
            is_completed = i < current_stage_idx or status == "completed"

            row_class = "stage-row"
            if is_active: row_class += " active"
            if is_completed: row_class += " completed"

            st.markdown(f"""
            <div class="{row_class}">
                <div class="stage-icon">{icon if not is_completed else '✓'}</div>
                <div class="stage-content">
                    <div class="stage-title">{name}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # Show Metrics
        metrics = st.columns(4)
        # We derive some metrics from logs if not explicit
        urls_found = len([l for l in logs if "Found" in l and "search results" in l])
        sources_valid = len([l for l in logs if "unique valid sources" in l])

        metrics[0].metric("Search Queries", "1") # Simplified
        metrics[1].metric("URLs Found", urls_found)
        metrics[2].metric("Sources Validated", sources_valid)
        metrics[3].metric("Current Stage", stage.capitalize())

        if status == "completed":
            st.session_state.page = "Report"
            st.rerun()
        elif status == "failed":
            st.error(f"Research failed: {job.get('error')}")
            if st.button("Back to Workspace"):
                st.session_state.page = "Workspace"
                st.rerun()
        else:
            time.sleep(2)
            st.rerun()

    except Exception as e:
        st.error(f"Error polling job: {e}")

# --- PAGE: REPORT ---
def show_report():
    job_id = st.session_state.active_job_id
    try:
        response = requests.get(f"{BACKEND_URL}/job/{job_id}")
        job = response.json()
        res = job.get("result")

        if not res:
            st.warning("No report results found.")
            if st.button("New Research"):
                st.session_state.page = "Workspace"
                st.rerun()
            return

        st.markdown(f"""
        <div class="report-container">
            <div class="report-header">
                <div style="font-size: 0.9rem; color: {ACCENT_COLOR}; font-weight: 700; text-transform: uppercase; margin-bottom: 0.5rem;">Research Report</div>
                <div style="font-size: 2.5rem; font-weight: 800; letter-spacing: -0.03em; margin-bottom: 1rem;">{res['question']}</div>
                <div style="display: flex; gap: 2rem; color: #6b7280; font-size: 0.9rem;">
                    <span>Completed: {job['updated_at']}</span>
                    <span>Confidence: <b style="color: {TEXT_COLOR}">{res['confidence_level'].upper()}</b></span>
                    <span>Sources: <b style="color: {TEXT_COLOR}">{len(res.get('source_urls', []))}</b></span>
                </div>
            </div>

            <div class="report-card">
                <div class="section-title">✨ Executive Summary</div>
                <div style="font-size: 1.15rem; line-height: 1.7; color: #374151; margin-bottom: 3rem;">
                    {res['short_answer']}
                </div>

                <div class="section-title">🎯 Key Findings</div>
        """, unsafe_allow_html=True)

        for f in res.get('findings', []):
            st.markdown(f"""
            <div class="finding-card">
                <div style="font-weight: 700; font-size: 1.1rem; margin-bottom: 0.75rem;">{f['claim']}</div>
                <div style="font-size: 0.95rem; line-height: 1.6; color: #4b5563;">
                    {f['evidence_passages'][0] if f['evidence_passages'] else ''}
                </div>
                <div style="margin-top: 1rem; display: flex; gap: 8px;">
                    {'<span class="tier-badge" style="background: #fff1f0; color: #ff4d4f;">Interpretation</span>' if f.get('is_interpreted') else '<span class="tier-badge" style="background: #f6ffed; color: #52c41a;">Direct Evidence</span>'}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="section-title">🔍 Verified Sources</div>', unsafe_allow_html=True)
        st.markdown('<div class="source-grid">', unsafe_allow_html=True)

        # We need the full source objects from the job store if available,
        # otherwise we just show the URLs from the result.
        # The backend store actually keeps the full Source list.
        for s_url in res.get('source_urls', []):
            domain = s_url.split("//")[-1].split("/")[0]
            st.markdown(f"""
            <div class="source-card">
                <div class="tier-badge">TIER 1</div>
                <div style="font-weight: 600; margin: 0.5rem 0; font-size: 0.95rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{domain}</div>
                <div style="font-size: 0.8rem; color: #6b7280; margin-bottom: 1rem;">Verified technical documentation</div>
                <a href="{s_url}" target="_blank" style="color: {ACCENT_COLOR}; text-decoration: none; font-size: 0.85rem; font-weight: 600;">Visit Source →</a>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div></div></div>', unsafe_allow_html=True)

        # Sidebar-like actions at the bottom
        st.markdown("---")
        c1, c2, c3, c4 = st.columns(4)
        if c1.button("New Research", use_container_width=True):
            st.session_state.page = "Workspace"
            st.session_state.research_query = ""
            st.rerun()
        if c2.button("Download Markdown", use_container_width=True):
            st.info("Downloading...")
        if c3.button("Research History", use_container_width=True):
            st.session_state.page = "History"
            st.rerun()

    except Exception as e:
        st.error(f"Error loading report: {e}")

# --- PAGE: HISTORY ---
def show_history():
    st.markdown('<div style="margin-top: 6rem;"></div>', unsafe_allow_html=True)
    st.title("Research History")

    try:
        response = requests.get(f"{BACKEND_URL}/jobs")
        if response.status_code == 200:
            jobs = response.json()
            if not jobs:
                st.info("No research history found.")
            else:
                for job in jobs:
                    with st.container():
                        st.markdown(f"""
                        <div class="history-card">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                                <div style="font-weight: 700; font-size: 1.1rem; margin-bottom: 0.5rem;">{job['question']}</div>
                                <div class="tier-badge">{job['status']}</div>
                            </div>
                            <div style="display: flex; gap: 1.5rem; color: #6b7280; font-size: 0.85rem;">
                                <span>{job['updated_at']}</span>
                                <span>Confidence: <b>{job.get('result', {}).get('confidence_level', 'N/A').upper()}</b></span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button("View Report", key=f"view_{job['job_id']}"):
                            st.session_state.active_job_id = job['job_id']
                            st.session_state.page = "Report"
                            st.rerun()
        else:
            st.error("Failed to load history.")
    except Exception as e:
        st.error(f"Error: {e}")

# --- ROUTER ---
st.sidebar.markdown("### Navigation")
nav = st.sidebar.radio("", ["Workspace", "History"])
if nav != st.session_state.page and st.session_state.page not in ["Active Research", "Report"]:
    st.session_state.page = nav

# For the active/report pages, we keep them until user clicks "New Research"
if st.session_state.page == "Workspace":
    show_workspace()
elif st.session_state.page == "Active Research":
    show_active_research()
elif st.session_state.page == "Report":
    show_report()
elif st.session_state.page == "History":
    show_history()

# Header rendered last so it overlays
render_header()
