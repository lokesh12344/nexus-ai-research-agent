import os
import time
from html import escape
from datetime import datetime
from typing import Any, Optional

import requests
import streamlit as st


BACKEND_URL = os.getenv("NEXUS_API_URL", "http://localhost:8000").rstrip("/")
POLL_INTERVAL_SECONDS = 3
REQUEST_TIMEOUT_SECONDS = 10
NAV_ITEMS = ("Dashboard", "New Research", "Research History", "Saved Reports", "Settings")
RESEARCH_STAGES = (
    ("created", "Request received"),
    ("planning", "Research planning"),
    ("searching", "Web search"),
    ("retrieving", "Content retrieval"),
    ("filtering", "Source filtering"),
    ("synthesizing", "AI synthesis"),
    ("done", "Research complete"),
)

st.set_page_config(
    page_title="Nexus AI — Research Workspace",
    page_icon="N",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
        :root {
            --bg: #0c0e12;
            --surface: #12151b;
            --surface-raised: #171b23;
            --border: #252a34;
            --muted: #939baa;
            --text: #edf0f5;
            --accent: #b7f36b;
            --accent-strong: #a4e457;
        }
        html, body, [class*="css"], [data-testid="stAppViewContainer"] {
            font-family: 'DM Sans', sans-serif;
        }
        .stApp { background: var(--bg); color: var(--text); }
        [data-testid="stHeader"] { background: rgba(12, 14, 18, .8); }
        [data-testid="stSidebar"] {
            background: #101218;
            border-right: 1px solid var(--border);
        }
        [data-testid="stSidebar"] > div:first-child { padding-top: 1.2rem; }
        [data-testid="stMain"] .block-container {
            max-width: 1240px;
            padding: 2.4rem 2.5rem 4rem;
        }
        h1, h2, h3 { font-family: 'Manrope', sans-serif !important; letter-spacing: -.035em; }
        h1 { font-size: clamp(1.8rem, 3vw, 2.6rem) !important; font-weight: 700 !important; }
        h2 { font-size: 1.45rem !important; font-weight: 700 !important; }
        h3 { font-size: 1.05rem !important; font-weight: 650 !important; }
        p, label, [data-testid="stCaptionContainer"] { color: #b5bdca; }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: var(--muted); }
        [data-testid="stSidebar"] .stButton > button {
            background: #191e27 !important;
            border: 1px solid #303846 !important;
            color: #edf0f5 !important;
            text-align: left;
            justify-content: flex-start;
            padding: .62rem .8rem;
            min-height: 2.55rem;
            transition: background .16s ease, border-color .16s ease, color .16s ease;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            background: #252c37 !important;
            border-color: #566174 !important;
            color: #ffffff !important;
        }
        [data-testid="stSidebar"] .stButton > button[kind="primary"] {
            background: #b7f36b !important;
            border-color: #b7f36b !important;
            color: #10140c !important;
        }
        .stButton > button, .stDownloadButton > button, .stLinkButton > a {
            background-color: #202631 !important;
            border: 1px solid #3b4554 !important;
            color: #f3f5f8 !important;
            border-radius: 9px;
            font-weight: 600;
            transition: transform .16s ease, border-color .16s ease, background .16s ease;
        }
        .stButton > button p, .stDownloadButton > button p,
        .stLinkButton > a p, .stFormSubmitButton > button p,
        [data-testid="stSidebar"] .stButton > button p {
            color: inherit !important;
        }
        .stButton > button:hover, .stDownloadButton > button:hover, .stLinkButton > a:hover {
            background-color: #2b3441 !important;
            border-color: #667387 !important;
            color: #ffffff !important;
            transform: translateY(-1px);
        }
        .stButton > button[kind="primary"], .stFormSubmitButton > button {
            background: #b7f36b !important;
            border-color: #b7f36b !important;
            color: #10140c !important;
        }
        .stButton > button[kind="primary"]:hover, .stFormSubmitButton > button:hover {
            background: #c8fa8a !important;
            border-color: #c8fa8a !important;
            color: #10140c !important;
        }
        [data-testid="stTextArea"] textarea, [data-testid="stTextInput"] input {
            background: #101319;
            border-color: #2a303b;
            border-radius: 10px;
            color: var(--text);
        }
        [data-testid="stTextArea"] textarea:focus, [data-testid="stTextInput"] input:focus {
            border-color: #819e5c;
            box-shadow: 0 0 0 1px #819e5c;
        }
        [data-testid="stMetric"] {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1rem 1.1rem;
        }
        [data-testid="stMetricLabel"] { color: var(--muted); }
        [data-testid="stMetricValue"] { color: var(--text); font-family: 'Manrope', sans-serif; }
        [data-testid="stExpander"] {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 10px;
        }
        .brand {
            display: flex; align-items: center; gap: .7rem;
            color: var(--text); font: 700 1.15rem 'Manrope', sans-serif;
            letter-spacing: -.04em; padding: 0 .4rem .8rem;
        }
        .brand-mark {
            display: grid; place-items: center; width: 31px; height: 31px;
            border-radius: 9px; background: var(--accent); color: #10140c;
            font-size: .82rem; font-weight: 800;
        }
        .eyebrow {
            color: var(--accent); text-transform: uppercase; letter-spacing: .12em;
            font-size: .72rem; font-weight: 700; margin-bottom: .5rem;
        }
        .hero-panel {
            background: radial-gradient(ellipse at 86% 0%, rgba(183,243,107,.09), transparent 38%), #12151b;
            border: 1px solid var(--border); border-radius: 16px;
            padding: clamp(1.3rem, 3vw, 2.2rem); margin: .4rem 0 1.5rem;
        }
        .hero-panel h1 { margin: .1rem 0 .5rem; }
        .hero-copy { color: #aeb6c4; max-width: 680px; line-height: 1.65; }
        .section-head {
            display: flex; align-items: center; justify-content: space-between;
            margin: 1.8rem 0 .8rem;
        }
        .section-head h3 { margin: 0; }
        .surface-card {
            background: var(--surface); border: 1px solid var(--border);
            border-radius: 12px; padding: 1.05rem 1.15rem; margin-bottom: .7rem;
        }
        .subtle { color: var(--muted); font-size: .88rem; }
        .status-pill {
            display: inline-flex; align-items: center; gap: .45rem;
            border: 1px solid var(--border); background: #171b22;
            color: #cbd2dd; border-radius: 999px; padding: .26rem .65rem;
            font-size: .76rem; font-weight: 600;
        }
        .status-dot {
            width: 7px; height: 7px; border-radius: 50%; display: inline-block;
            background: #8992a1;
        }
        .status-dot.ok { background: var(--accent); }
        .status-dot.warn { background: #f0b65a; }
        .status-dot.bad { background: #f07878; }
        .stage-item {
            display: flex; gap: .8rem; align-items: flex-start;
            padding: .7rem .2rem; border-bottom: 1px solid #20242c;
        }
        .stage-item:last-child { border-bottom: 0; }
        .stage-marker {
            width: 20px; height: 20px; flex: 0 0 20px; display: grid;
            place-items: center; border: 1px solid #3a414e; border-radius: 50%;
            color: #7f8998; font-size: .68rem; margin-top: .05rem;
        }
        .stage-marker.active { border-color: var(--accent); color: #11150d; background: var(--accent); }
        .stage-marker.complete { border-color: #668d3b; color: var(--accent); }
        .stage-label { color: #aeb6c4; font-size: .9rem; }
        .stage-label.active { color: var(--text); font-weight: 600; }
        .finding {
            background: var(--surface); border: 1px solid var(--border);
            border-radius: 12px; padding: 1.2rem; margin: .75rem 0;
        }
        .finding-claim { color: var(--text); font-weight: 650; line-height: 1.55; }
        .citation {
            display: inline-block; border: 1px solid #343b48; border-radius: 6px;
            padding: .18rem .48rem; margin: .35rem .3rem 0 0;
            color: var(--accent); font-size: .78rem; text-decoration: none;
        }
        .citation:hover { border-color: var(--accent); }
        .empty-state {
            background: #11141a; border: 1px dashed #343b48; border-radius: 12px;
            padding: 1.4rem; color: #aeb6c4;
        }
        hr { border-color: var(--border); }
        @media (max-width: 760px) {
            [data-testid="stMain"] .block-container { padding: 1.5rem 1rem 3rem; }
            [data-testid="stSidebar"] { min-width: 225px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def api_request(method: str, path: str, **kwargs: Any) -> tuple[Optional[Any], Optional[str]]:
    try:
        response = requests.request(
            method,
            f"{BACKEND_URL}{path}",
            timeout=REQUEST_TIMEOUT_SECONDS,
            **kwargs,
        )
    except requests.ConnectionError:
        return None, f"Could not connect to Nexus API at {BACKEND_URL}."
    except requests.Timeout:
        return None, "The Nexus API did not respond in time. Please try again."
    except requests.RequestException:
        return None, "The request to the Nexus API could not be completed."

    if not response.ok:
        if response.status_code == 404:
            return None, "This job is not available yet. Refresh in a moment, or return to the dashboard."
        return None, f"The Nexus API returned HTTP {response.status_code}. Please try again."

    try:
        return response.json(), None
    except ValueError:
        return None, "The Nexus API returned an unreadable response."


def get_jobs() -> tuple[list[dict[str, Any]], Optional[str]]:
    data, error = api_request("GET", "/jobs")
    if error:
        return [], error
    if not isinstance(data, list):
        return [], "The Nexus API returned an unexpected job list."
    return [job for job in data if isinstance(job, dict)], None


def format_timestamp(value: Any) -> str:
    if not isinstance(value, str) or not value:
        return "Not available"
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone().strftime("%b %d, %Y · %I:%M %p")
    except ValueError:
        return value


def status_class(status: Any) -> str:
    if status == "completed":
        return "ok"
    if status == "failed":
        return "bad"
    if status in ("queued", "running"):
        return "warn"
    return ""


def status_pill(status: Any) -> str:
    label = escape(str(status or "unknown").replace("_", " ").title())
    css_class = status_class(status)
    return (
        f'<span class="status-pill"><span class="status-dot {css_class}"></span>'
        f"{label}</span>"
    )


def section_heading(title: str, note: Optional[str] = None) -> None:
    st.markdown('<div class="section-head">', unsafe_allow_html=True)
    st.markdown(f"<h3>{title}</h3>", unsafe_allow_html=True)
    if note:
        st.caption(note)
    st.markdown("</div>", unsafe_allow_html=True)


def open_job(job: dict[str, Any]) -> None:
    st.session_state.active_job_id = job.get("job_id")
    st.session_state.page = "Report" if job.get("status") == "completed" else "Research Progress"
    st.rerun()


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            '<div class="brand"><span class="brand-mark">N</span> Nexus AI</div>',
            unsafe_allow_html=True,
        )
        st.caption("RESEARCH WORKSPACE")
        if st.button("＋  New research", type="primary", use_container_width=True, key="new_research_nav"):
            st.session_state.page = "New Research"
            st.rerun()
        st.markdown("")
        for item in NAV_ITEMS:
            icon = {
                "Dashboard": "⌂",
                "New Research": "＋",
                "Research History": "◷",
                "Saved Reports": "▤",
                "Settings": "⚙",
            }[item]
            if st.button(
                f"{icon}  {item}",
                type="primary" if st.session_state.page == item else "secondary",
                use_container_width=True,
                key=f"nav_{item}",
            ):
                st.session_state.page = item
                st.rerun()
        st.markdown("---")
        health, error = api_request("GET", "/health")
        if error:
            st.markdown(
                '<span class="status-pill"><span class="status-dot bad"></span>API unavailable</span>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<span class="status-pill"><span class="status-dot ok"></span>API connected</span>',
                unsafe_allow_html=True,
            )
        st.caption("Service status reflects the backend health endpoint.")


def render_dashboard() -> None:
    st.markdown(
        """
        <div class="hero-panel">
            <div class="eyebrow">Nexus AI · Research workspace</div>
            <h1>Research with evidence.</h1>
            <div class="hero-copy">Turn a question into a structured report grounded in web sources.
            Review what is running, revisit completed research, and follow each job's actual progress.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("＋  Start new research", type="primary", key="dashboard_new"):
        st.session_state.page = "New Research"
        st.rerun()

    jobs, error = get_jobs()
    if error:
        st.error(error)
        st.info("The dashboard needs the FastAPI backend to load research activity.")
        return

    completed = [job for job in jobs if job.get("status") == "completed"]
    running = [job for job in jobs if job.get("status") in ("queued", "running")]
    failed = [job for job in jobs if job.get("status") == "failed"]
    metrics = st.columns(4)
    metrics[0].metric("Total research", len(jobs))
    metrics[1].metric("Completed", len(completed))
    metrics[2].metric("In progress", len(running))
    metrics[3].metric("Failed", len(failed))

    left, right = st.columns([1.2, 1])
    with left:
        section_heading("Recent activity", "Latest jobs returned by the research API")
        if not jobs:
            st.markdown(
                '<div class="empty-state">No research yet. Start with a question to create your first report.</div>',
                unsafe_allow_html=True,
            )
        for job in jobs[:5]:
            st.markdown(status_pill(job.get("status")), unsafe_allow_html=True)
            question = job.get("question") or "Untitled research"
            st.markdown(f"**{question}**")
            st.caption(
                f"Updated {format_timestamp(job.get('updated_at'))} · "
                f"Stage: {job.get('current_stage') or 'Unknown'}"
            )
            if st.button("Open job", key=f"recent_{job.get('job_id')}"):
                open_job(job)
    with right:
        section_heading("Latest reports", "Completed research")
        if not completed:
            st.markdown(
                '<div class="empty-state">Completed reports will appear here.</div>',
                unsafe_allow_html=True,
            )
        for job in completed[:4]:
            st.markdown(f"**{job.get('question') or 'Untitled research'}**")
            result = job.get("result") or {}
            confidence = result.get("confidence_level")
            st.caption(
                f"Updated {format_timestamp(job.get('updated_at'))}"
                + (f" · {str(confidence).title()} confidence" if confidence else "")
            )
            if st.button("View report", key=f"report_{job.get('job_id')}"):
                open_job(job)


def render_new_research() -> None:
    st.markdown('<div class="eyebrow">New research</div>', unsafe_allow_html=True)
    st.title("What do you want to understand?")
    st.markdown(
        '<p class="hero-copy">A focused question helps Nexus find relevant sources and produce a clearer, evidence-backed response.</p>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="surface-card">', unsafe_allow_html=True)
    with st.form("research_request_form", clear_on_submit=False):
        question = st.text_area(
            "Research topic",
            placeholder="e.g. Compare the trade-offs of RAG and fine-tuning for enterprise AI systems",
            height=150,
            key="research_topic",
        )
        st.caption(
            "The current API accepts a research question only. Context, source preferences, "
            "and additional configuration are not supported."
        )
        submitted = st.form_submit_button("Start research", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if submitted:
        topic = question.strip()
        if not topic:
            st.warning("Enter a research question to continue.")
            return
        with st.spinner("Creating your research job…"):
            payload, error = api_request("POST", "/research", json={"question": topic})
        if error:
            st.error(error)
            return
        job_id = payload.get("job_id") if isinstance(payload, dict) else None
        if not job_id:
            st.error("The API did not return a job ID. No research job was opened.")
            return
        st.session_state.active_job_id = job_id
        st.session_state.page = "Research Progress"
        st.session_state.auto_refresh = True
        st.rerun()


def render_progress(job: dict[str, Any]) -> None:
    status = job.get("status", "unknown")
    stage = job.get("current_stage", "unknown")
    if status == "failed":
        st.error(job.get("error") or "The research job failed. The backend did not provide an error detail.")
    elif status in ("queued", "running"):
        st.info("Research is in progress. This view uses the job status and stage reported by the backend.")

    st.markdown('<div class="surface-card">', unsafe_allow_html=True)
    cols = st.columns([1, 1, 2])
    cols[0].markdown("**Status**")
    cols[0].markdown(status_pill(status), unsafe_allow_html=True)
    cols[1].markdown("**Current stage**")
    cols[1].write(str(stage).replace("_", " ").title())
    cols[2].markdown("**Job ID**")
    cols[2].code(str(job.get("job_id", "")), language=None)
    st.markdown("</div>", unsafe_allow_html=True)

    stage_ids = [item[0] for item in RESEARCH_STAGES]
    current_index = stage_ids.index(stage) if stage in stage_ids else -1
    section_heading("Research lifecycle", "Only stages reported by the existing agent are shown")
    st.markdown('<div class="surface-card">', unsafe_allow_html=True)
    for index, (stage_id, label) in enumerate(RESEARCH_STAGES):
        is_complete = status == "completed" or (current_index >= 0 and index < current_index)
        is_active = status in ("queued", "running") and stage_id == stage
        marker_class = "complete" if is_complete else "active" if is_active else ""
        marker = "✓" if is_complete else "•" if is_active else str(index + 1)
        label_class = "active" if is_active else ""
        st.markdown(
            f'<div class="stage-item"><span class="stage-marker {marker_class}">{marker}</span>'
            f'<span class="stage-label {label_class}">{escape(label)}</span></div>',
            unsafe_allow_html=True,
        )
    if current_index < 0 and status not in ("failed", "completed"):
        st.caption(f"Current backend stage: {stage}")
    st.markdown("</div>", unsafe_allow_html=True)

    logs = job.get("logs") or []
    if logs:
        with st.expander(f"Job activity ({len(logs)} log entries)"):
            for entry in logs:
                st.text(str(entry))

    if status == "completed":
        st.success("Research completed.")
        if st.button("Open research report", type="primary"):
            st.session_state.page = "Report"
            st.rerun()
    elif status == "failed":
        if st.button("Retry job", type="primary"):
            payload, error = api_request("POST", f"/job/{job.get('job_id')}/resume")
            if error:
                st.error(error)
            elif isinstance(payload, dict) and payload.get("status") == "already_completed":
                st.session_state.page = "Report"
                st.rerun()
            else:
                st.session_state.auto_refresh = True
                st.rerun()
    else:
        cols = st.columns([1, 1, 3])
        cols[0].button("Refresh status", key="refresh_job")
        auto_refresh = cols[1].checkbox(
            "Auto-refresh",
            value=st.session_state.get("auto_refresh", True),
            key="auto_refresh",
        )
        if auto_refresh:
            time.sleep(POLL_INTERVAL_SECONDS)
            st.rerun()


def render_research_progress() -> None:
    st.markdown('<div class="eyebrow">Research job</div>', unsafe_allow_html=True)
    st.title("Research progress")
    job_id = st.session_state.get("active_job_id")
    if not job_id:
        st.warning("Choose a research job from history, or start a new one.")
        if st.button("Go to dashboard"):
            st.session_state.page = "Dashboard"
            st.rerun()
        return

    job, error = api_request("GET", f"/job/{job_id}")
    if error:
        st.error(error)
        if st.button("Try again"):
            st.rerun()
        return
    if not isinstance(job, dict):
        st.error("The API returned an unexpected job response.")
        return
    st.markdown(f"**{job.get('question') or 'Research job'}**")
    render_progress(job)


def build_report_markdown(result: dict[str, Any], job: dict[str, Any]) -> str:
    lines = [
        f"# {result.get('question') or 'Research report'}",
        "",
        f"Status: {job.get('status', 'unknown')}",
        f"Updated: {format_timestamp(job.get('updated_at'))}",
        f"Confidence: {result.get('confidence_level', 'not provided')}",
        "",
        "## Executive summary",
        "",
        result.get("short_answer") or "No summary was provided.",
        "",
        "## Findings",
        "",
    ]
    for index, finding in enumerate(result.get("findings") or [], start=1):
        lines.extend([f"### {index}. {finding.get('claim', 'Finding')}", ""])
        for passage in finding.get("evidence_passages") or []:
            lines.extend([f"> {passage}", ""])
        urls = finding.get("supporting_urls") or []
        if urls:
            lines.extend(["Supporting sources: " + ", ".join(str(url) for url in urls), ""])
    lines.extend(["## Sources", ""])
    lines.extend(f"- {url}" for url in result.get("source_urls") or [])
    for section in ("assumptions", "limitations", "unanswered_questions"):
        values = result.get(section) or []
        if values:
            lines.extend(["", f"## {section.replace('_', ' ').title()}", ""])
            lines.extend(f"- {item}" for item in values)
    return "\n".join(lines).strip() + "\n"


def render_report(job: dict[str, Any]) -> None:
    result = job.get("result")
    if not isinstance(result, dict):
        st.warning("This job does not have a report available yet.")
        if job.get("error"):
            st.error(job["error"])
        if st.button("View job progress"):
            st.session_state.page = "Research Progress"
            st.rerun()
        return

    st.markdown('<div class="eyebrow">Research report</div>', unsafe_allow_html=True)
    st.title(result.get("question") or "Research report")
    confidence = result.get("confidence_level")
    st.markdown(
        f"{status_pill(job.get('status'))} &nbsp; "
        f'<span class="subtle">Updated {format_timestamp(job.get("updated_at"))}</span>',
        unsafe_allow_html=True,
    )
    if confidence:
        st.caption(f"Confidence: {str(confidence).replace('_', ' ').title()}")

    st.markdown("---")
    section_heading("Executive summary")
    summary = result.get("short_answer")
    if summary:
        st.markdown(summary)
    else:
        st.info("The backend did not return an executive summary.")

    breakdown = result.get("confidence_breakdown")
    if isinstance(breakdown, dict):
        section_heading("Confidence breakdown", "Heuristic values returned by the research agent")
        cols = st.columns(len(breakdown) or 1)
        for column, (key, value) in zip(cols, breakdown.items()):
            column.metric(key.replace("_", " ").title(), f"{value:.0%}" if isinstance(value, (float, int)) else str(value))

    findings = result.get("findings") or []
    section_heading("Findings", f"{len(findings)} finding(s) returned by the agent")
    if not findings:
        st.markdown(
            '<div class="empty-state">No structured findings were returned for this research.</div>',
            unsafe_allow_html=True,
        )
    for index, finding in enumerate(findings, start=1):
        st.markdown('<div class="finding">', unsafe_allow_html=True)
        st.markdown(f"**{index}. {finding.get('claim') or 'Finding'}**")
        st.caption("Interpretation" if finding.get("is_interpreted") else "Directly supported")
        for passage in finding.get("evidence_passages") or []:
            st.markdown(f"> {passage}")
        urls = finding.get("supporting_urls") or []
        if urls:
            st.caption("Supporting sources")
            for source_index, url in enumerate(urls, start=1):
                st.link_button(
                    f"Source {source_index}",
                    str(url),
                    key=f"finding_{index}_source_{source_index}",
                )
        st.markdown("</div>", unsafe_allow_html=True)

    source_urls = result.get("source_urls") or []
    section_heading("Source references", f"{len(source_urls)} URL(s) supplied in the report")
    if source_urls:
        for index, url in enumerate(source_urls, start=1):
            st.link_button(
                f"{index}. {url}",
                str(url),
                use_container_width=True,
                key=f"report_source_{index}",
            )
    else:
        st.info("No source URLs were returned.")

    for label, key in (
        ("Assumptions", "assumptions"),
        ("Limitations", "limitations"),
        ("Unanswered questions", "unanswered_questions"),
    ):
        values = result.get(key) or []
        if values:
            section_heading(label)
            for value in values:
                st.markdown(f"- {value}")

    markdown = build_report_markdown(result, job)
    filename = f"nexus-research-{job.get('job_id', 'report')}.md"
    col_copy, col_download = st.columns([1, 1])
    with col_copy:
        st.code(markdown, language="markdown")
    with col_download:
        st.download_button(
            "Download Markdown report",
            data=markdown,
            file_name=filename,
            mime="text/markdown",
            use_container_width=True,
        )


def render_report_page() -> None:
    st.markdown('<div class="eyebrow">Library</div>', unsafe_allow_html=True)
    job_id = st.session_state.get("active_job_id")
    if not job_id:
        st.title("Research report")
        st.info("Select a completed report from history.")
        return
    job, error = api_request("GET", f"/job/{job_id}")
    if error:
        st.title("Research report")
        st.error(error)
        if st.button("Try again"):
            st.rerun()
        return
    if isinstance(job, dict):
        render_report(job)
    else:
        st.error("The API returned an unexpected job response.")


def render_job_table(jobs: list[dict[str, Any]], key_prefix: str) -> None:
    if not jobs:
        st.markdown(
            '<div class="empty-state">No matching research jobs were found.</div>',
            unsafe_allow_html=True,
        )
        return
    for job in jobs:
        job_id = job.get("job_id", "")
        st.markdown('<div class="surface-card">', unsafe_allow_html=True)
        cols = st.columns([5, 1.4, 1.5])
        cols[0].markdown(f"**{job.get('question') or 'Untitled research'}**")
        cols[0].caption(f"Job ID · `{job_id}`")
        cols[0].caption(
            f"Last updated {format_timestamp(job.get('updated_at'))} · "
            f"Stage: {job.get('current_stage') or 'Unknown'}"
        )
        cols[1].markdown(status_pill(job.get("status")), unsafe_allow_html=True)
        if job.get("result") and isinstance(job["result"], dict):
            confidence = job["result"].get("confidence_level")
            if confidence:
                cols[1].caption(f"{str(confidence).title()} confidence")
        if cols[2].button("Open", key=f"{key_prefix}_{job_id}"):
            open_job(job)
        st.markdown("</div>", unsafe_allow_html=True)


def render_history() -> None:
    st.markdown('<div class="eyebrow">Library</div>', unsafe_allow_html=True)
    st.title("Research history")
    st.caption("Search by topic or job ID and filter using the status returned by the API.")
    jobs, error = get_jobs()
    if error:
        st.error(error)
        return
    search_col, status_col = st.columns([2, 1])
    query = search_col.text_input("Search research", placeholder="Topic or job ID")
    statuses = ["All statuses"] + sorted({str(job.get("status", "unknown")) for job in jobs})
    selected_status = status_col.selectbox("Status", statuses)
    filtered = jobs
    if query:
        needle = query.casefold()
        filtered = [
            job for job in filtered
            if needle in str(job.get("question", "")).casefold()
            or needle in str(job.get("job_id", "")).casefold()
        ]
    if selected_status != "All statuses":
        filtered = [job for job in filtered if job.get("status") == selected_status]
    section_heading("All research", f"{len(filtered)} job(s)")
    render_job_table(filtered, "history")


def render_saved_reports() -> None:
    st.markdown('<div class="eyebrow">Library</div>', unsafe_allow_html=True)
    st.title("Saved reports")
    st.caption("Completed reports available from the persisted job history.")
    jobs, error = get_jobs()
    if error:
        st.error(error)
        return
    reports = [
        job for job in jobs
        if job.get("status") == "completed" and isinstance(job.get("result"), dict)
    ]
    render_job_table(reports, "saved")


def render_settings() -> None:
    st.markdown('<div class="eyebrow">Workspace</div>', unsafe_allow_html=True)
    st.title("Settings")
    st.caption("Service information available through the existing Nexus API.")
    health, error = api_request("GET", "/health")
    st.markdown('<div class="surface-card">', unsafe_allow_html=True)
    st.subheader("Backend service")
    st.write(f"API endpoint: `{BACKEND_URL}`")
    if error:
        st.error(error)
    elif isinstance(health, dict) and health.get("status") == "ok":
        st.success("FastAPI health check: operational")
    else:
        st.warning("The health endpoint responded with an unrecognized status.")
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div class="surface-card">', unsafe_allow_html=True)
    st.subheader("Research integrations")
    st.write(
        "Gemini and Firecrawl are configured server-side. The current health endpoint "
        "does not report their individual availability, quota, or credential status."
    )
    st.markdown("</div>", unsafe_allow_html=True)
    st.caption("API keys and environment variables are not read or displayed in the frontend.")


def main() -> None:
    inject_styles()
    if "page" not in st.session_state:
        st.session_state.page = "Dashboard"
    if "active_job_id" not in st.session_state:
        st.session_state.active_job_id = None
    render_sidebar()
    page = st.session_state.page
    if page == "Dashboard":
        render_dashboard()
    elif page == "New Research":
        render_new_research()
    elif page == "Research Progress":
        render_research_progress()
    elif page == "Report":
        render_report_page()
    elif page == "Research History":
        render_history()
    elif page == "Saved Reports":
        render_saved_reports()
    elif page == "Settings":
        render_settings()
    else:
        st.session_state.page = "Dashboard"
        st.rerun()


main()
