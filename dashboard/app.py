"""LeadRet — Streamlit Dashboard (Terminal Style)"""
import subprocess
import sys
import threading
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from streamlit_star_rating import st_star_rating

from src.storage.database import init_db, get_connection
from src.storage.lead_store import (
    get_feed,
    get_rated_leads,
    get_lead,
    set_rating,
    update_lead,
    delete_lead,
    count_leads,
    block_company,
    unblock_company,
    get_blocked_companies,
)
from src.models.campaign import list_campaigns, load_campaign
from src.config import RESEARCH_PROVIDER, GEMINI_API_KEY, PERPLEXITY_API_KEY, GROK_API_KEY

st.set_page_config(page_title="LeadRet", page_icon="🔍", layout="wide")
init_db()

# ---------------------------------------------------------------------------
# Theme CSS
# ---------------------------------------------------------------------------
PIPBOY_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&display=swap');
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background-color: #0a0e14 !important; color: #33ff33 !important;
    font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace !important;
}
[data-testid="stHeader"], header[data-testid="stHeader"] { background-color: #0a0e14 !important; }
[data-testid="stToolbar"] { background-color: #0a0e14 !important; }
[data-testid="stSidebar"] { background-color: #0d1117 !important; border-right: 1px solid #1a3a1a !important; }
[data-testid="stSidebar"] * { font-family: 'JetBrains Mono', monospace !important; }
[data-testid="stSidebarCollapseButton"] { display: none !important; }
h1, h2, h3, h4, h5, h6,
[data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3 {
    color: #00ff00 !important; font-family: 'JetBrains Mono', monospace !important;
    font-weight: 600 !important; text-transform: uppercase !important;
}
[data-testid="stMarkdownContainer"] h2 { color: #00cc00 !important; }
[data-testid="stMarkdownContainer"] strong { text-transform: uppercase !important; }
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li {
    color: #33ff33 !important; font-family: 'JetBrains Mono', monospace !important; font-size: 0.85rem !important;
}
[data-testid="stMarkdownContainer"] strong { color: #66ff66 !important; }
[data-testid="stMarkdownContainer"] em { color: #22aa22 !important; }
[data-testid="stMarkdownContainer"] code { color: #00ff88 !important; background-color: #0a1a0a !important; }
[data-testid="stMarkdownContainer"] a {
    color: #00ffaa !important; text-decoration: none !important; overflow: hidden !important;
    text-overflow: ellipsis !important; white-space: nowrap !important; display: inline-block !important;
    max-width: 100% !important; vertical-align: bottom !important;
}
[data-testid="stMarkdownContainer"] a:hover { color: #88ffcc !important; text-decoration: underline !important; }
[data-testid="stCaptionContainer"] { color: #1a8a1a !important; font-family: 'JetBrains Mono', monospace !important; text-transform: uppercase !important; }
[data-testid="stMetric"] { background-color: #0a1a0a !important; border: 1px solid #1a3a1a !important; border-radius: 4px !important; padding: 12px !important; }
[data-testid="stMetricLabel"] { color: #1a8a1a !important; font-family: 'JetBrains Mono', monospace !important; font-size: 0.75rem !important; }
[data-testid="stMetricValue"] { color: #00ff00 !important; font-family: 'JetBrains Mono', monospace !important; }
[data-testid="stBaseButton-secondary"] {
    background-color: #0a1a0a !important; color: #33ff33 !important; border: 1px solid #1a3a1a !important;
    font-family: 'JetBrains Mono', monospace !important; font-size: 0.8rem !important; border-radius: 3px !important; transition: all 0.15s ease !important;
}
[data-testid="stBaseButton-secondary"]:hover { background-color: #0d2a0d !important; border-color: #00ff00 !important; color: #00ff00 !important; }
[data-testid="stBaseButton-primary"] {
    background-color: #00aa00 !important; color: #0a0e14 !important; border: none !important;
    font-family: 'JetBrains Mono', monospace !important; font-weight: 600 !important; font-size: 0.8rem !important; border-radius: 3px !important;
}
[data-testid="stBaseButton-primary"]:hover { background-color: #00cc00 !important; }
[data-testid="stSelectbox"] label, [data-testid="stTextArea"] label {
    color: #1a8a1a !important; font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.75rem !important; text-transform: uppercase !important; letter-spacing: 0.05em !important;
}
[data-testid="stSelectbox"] > div > div, [data-testid="stTextArea"] textarea, [data-testid="stTextInput"] input {
    background-color: #0a1a0a !important; color: #33ff33 !important; border: 1px solid #1a3a1a !important;
    font-family: 'JetBrains Mono', monospace !important; font-size: 0.85rem !important; border-radius: 3px !important;
}
[data-testid="stTextInput"] input::placeholder { color: #1a5a1a !important; }
[data-testid="stTextInput"] input:focus { border-color: #00ff00 !important; box-shadow: 0 0 0 1px #00ff0033 !important; }
[data-baseweb="popover"] { background-color: #0a1a0a !important; border: 1px solid #1a3a1a !important; }
[data-baseweb="popover"] ul { background-color: #0a1a0a !important; }
[data-baseweb="popover"] li { background-color: #0a1a0a !important; color: #33ff33 !important; font-family: 'JetBrains Mono', monospace !important; }
[data-baseweb="popover"] li:hover, [data-baseweb="popover"] li[aria-selected="true"] { background-color: #0d2a0d !important; color: #00ff00 !important; }
[data-baseweb="popover"] [data-baseweb="menu"] { background-color: #0a1a0a !important; }
[data-testid="stTextArea"] textarea::placeholder { color: #1a5a1a !important; }
[data-testid="stTextArea"] textarea:focus { border-color: #00ff00 !important; box-shadow: 0 0 0 1px #00ff0033 !important; }
hr { border-color: #1a3a1a !important; }
[data-testid="stAlert"] { background-color: #0a1a0a !important; border: 1px solid #1a3a1a !important; font-family: 'JetBrains Mono', monospace !important; border-radius: 3px !important; color: #33ff33 !important; }
[data-testid="stCode"] { background-color: #0a1a0a !important; border: 1px solid #1a3a1a !important; }
[data-testid="stSpinner"] { color: #00ff00 !important; }
[data-testid="stProgress"] > div > div > div { background-color: #00ff00 !important; }
[data-testid="stProgress"] > div > div { background-color: #1a3a1a !important; }
[data-testid="stStatusWidget"] button { background-color: #0a1a0a !important; color: #00ff00 !important; border-color: #1a3a1a !important; }
[data-testid="stStatusWidget"] button:hover { background-color: #0d2a0d !important; border-color: #00ff00 !important; }
[data-testid="stStatusWidget"] svg { fill: #00ff00 !important; color: #00ff00 !important; }
[data-testid="stStatusWidget"] span, [data-testid="stStatusWidget"] label { color: #00ff00 !important; }
[data-testid="stToolbar"] button { color: #00ff00 !important; }
[data-testid="stToolbar"] button:hover { color: #00ff00 !important; background-color: #0d2a0d !important; }
[data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"] { border-color: #1a3a1a !important; }
[data-testid="stHorizontalBlock"] { margin-bottom: -0.5rem !important; }
[data-testid="stExpander"] { background-color: transparent !important; border: none !important; margin-top: -0.5rem !important; }
[data-testid="stExpander"] details { background-color: transparent !important; border: none !important; }
[data-testid="stExpander"] summary { font-size: 0.65rem !important; color: #1a6a1a !important; font-family: 'JetBrains Mono', monospace !important; padding: 0 !important; background-color: transparent !important; }
[data-testid="stExpander"] summary span { font-size: 0.65rem !important; color: #1a6a1a !important; background-color: transparent !important; }
[data-testid="stExpander"] summary svg { width: 0.65rem !important; height: 0.65rem !important; fill: #1a6a1a !important; }
[data-testid="stExpander"] summary:hover, [data-testid="stExpander"] summary:hover span { color: #33ff33 !important; }
[data-testid="stExpander"] summary:hover svg { fill: #33ff33 !important; }
[data-testid="stExpander"] summary:focus, [data-testid="stExpander"] summary:active,
[data-testid="stExpander"] summary:focus span, [data-testid="stExpander"] summary:active span {
    color: #1a6a1a !important; background-color: transparent !important; outline: none !important; box-shadow: none !important;
}
[data-testid="stExpander"] [data-testid="stExpanderDetails"] { background-color: transparent !important; border: none !important; padding: 0 0 0 0.5rem !important; }
::-webkit-scrollbar { display: none; }
* { -ms-overflow-style: none; scrollbar-width: none; }
code.red-badge { color: #ff3333 !important; }</style>
"""

CLEAN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&display=swap');
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background-color: #f5f5f7 !important; color: #1d1d1f !important;
    font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace !important;
}
[data-testid="stHeader"], header[data-testid="stHeader"] { background-color: #f5f5f7 !important; }
[data-testid="stToolbar"] { background-color: #f5f5f7 !important; }
[data-testid="stSidebar"] { background-color: #eeeef0 !important; border-right: 1px solid #d1d1d6 !important; }
[data-testid="stSidebar"] * { font-family: 'JetBrains Mono', monospace !important; }
[data-testid="stSidebarCollapseButton"] { display: none !important; }
h1, h2, h3, h4, h5, h6,
[data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3 {
    color: #1d1d1f !important; font-family: 'JetBrains Mono', monospace !important;
    font-weight: 600 !important; text-transform: uppercase !important;
}
[data-testid="stMarkdownContainer"] h2 { color: #3a3a3c !important; }
[data-testid="stMarkdownContainer"] strong { text-transform: uppercase !important; }
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li {
    color: #3a3a3c !important; font-family: 'JetBrains Mono', monospace !important; font-size: 0.85rem !important;
}
[data-testid="stMarkdownContainer"] strong { color: #1d1d1f !important; }
[data-testid="stMarkdownContainer"] em { color: #636366 !important; }
[data-testid="stMarkdownContainer"] code { color: #6ba3d6 !important; background-color: #e8edf3 !important; }
[data-testid="stMarkdownContainer"] a {
    color: #6ba3d6 !important; text-decoration: none !important; overflow: hidden !important;
    text-overflow: ellipsis !important; white-space: nowrap !important; display: inline-block !important;
    max-width: 100% !important; vertical-align: bottom !important;
}
[data-testid="stMarkdownContainer"] a:hover { color: #5a93c6 !important; text-decoration: underline !important; }
[data-testid="stCaptionContainer"] { color: #86868b !important; font-family: 'JetBrains Mono', monospace !important; text-transform: uppercase !important; }
[data-testid="stMetric"] { background-color: #ffffff !important; border: 1px solid #d1d1d6 !important; border-radius: 4px !important; padding: 12px !important; }
[data-testid="stMetricLabel"] { color: #86868b !important; font-family: 'JetBrains Mono', monospace !important; font-size: 0.75rem !important; }
[data-testid="stMetricValue"] { color: #1d1d1f !important; font-family: 'JetBrains Mono', monospace !important; }
[data-testid="stBaseButton-secondary"] {
    background-color: #ffffff !important; color: #3a3a3c !important; border: 1px solid #d1d1d6 !important;
    font-family: 'JetBrains Mono', monospace !important; font-size: 0.8rem !important; border-radius: 3px !important; transition: all 0.15s ease !important;
}
[data-testid="stBaseButton-secondary"]:hover { background-color: #eeeef0 !important; border-color: #6ba3d6 !important; color: #6ba3d6 !important; }
[data-testid="stBaseButton-primary"] {
    background-color: #6ba3d6 !important; color: #ffffff !important; border: none !important;
    font-family: 'JetBrains Mono', monospace !important; font-weight: 600 !important; font-size: 0.8rem !important; border-radius: 3px !important;
}
[data-testid="stBaseButton-primary"]:hover { background-color: #5a93c6 !important; }
[data-testid="stSelectbox"] label, [data-testid="stTextArea"] label {
    color: #86868b !important; font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.75rem !important; text-transform: uppercase !important; letter-spacing: 0.05em !important;
}
[data-testid="stSelectbox"] > div > div, [data-testid="stTextArea"] textarea, [data-testid="stTextInput"] input {
    background-color: #ffffff !important; color: #1d1d1f !important; border: 1px solid #d1d1d6 !important;
    font-family: 'JetBrains Mono', monospace !important; font-size: 0.85rem !important; border-radius: 3px !important;
}
[data-testid="stTextInput"] input::placeholder { color: #aeaeb2 !important; }
[data-testid="stTextInput"] input:focus { border-color: #6ba3d6 !important; box-shadow: 0 0 0 1px #6ba3d633 !important; }
[data-baseweb="popover"] { background-color: #ffffff !important; border: 1px solid #d1d1d6 !important; }
[data-baseweb="popover"] ul { background-color: #ffffff !important; }
[data-baseweb="popover"] li { background-color: #ffffff !important; color: #1d1d1f !important; font-family: 'JetBrains Mono', monospace !important; }
[data-baseweb="popover"] li:hover, [data-baseweb="popover"] li[aria-selected="true"] { background-color: #e8edf3 !important; color: #6ba3d6 !important; }
[data-baseweb="popover"] [data-baseweb="menu"] { background-color: #ffffff !important; }
[data-testid="stTextArea"] textarea::placeholder { color: #aeaeb2 !important; }
[data-testid="stTextArea"] textarea:focus { border-color: #6ba3d6 !important; box-shadow: 0 0 0 1px #6ba3d633 !important; }
hr { border-color: #d1d1d6 !important; }
[data-testid="stAlert"] { background-color: #ffffff !important; border: 1px solid #d1d1d6 !important; font-family: 'JetBrains Mono', monospace !important; border-radius: 3px !important; color: #3a3a3c !important; }
[data-testid="stCode"] { background-color: #ffffff !important; border: 1px solid #d1d1d6 !important; }
[data-testid="stSpinner"] { color: #6ba3d6 !important; }
[data-testid="stProgress"] > div > div > div { background-color: #6ba3d6 !important; }
[data-testid="stProgress"] > div > div { background-color: #d1d1d6 !important; }
[data-testid="stStatusWidget"] button { background-color: #ffffff !important; color: #6ba3d6 !important; border-color: #d1d1d6 !important; }
[data-testid="stStatusWidget"] button:hover { background-color: #e8edf3 !important; border-color: #6ba3d6 !important; }
[data-testid="stStatusWidget"] svg { fill: #6ba3d6 !important; color: #6ba3d6 !important; }
[data-testid="stStatusWidget"] span, [data-testid="stStatusWidget"] label { color: #6ba3d6 !important; }
[data-testid="stToolbar"] button { color: #86868b !important; }
[data-testid="stToolbar"] button:hover { color: #6ba3d6 !important; background-color: #eeeef0 !important; }
[data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"] { border-color: #d1d1d6 !important; }
[data-testid="stHorizontalBlock"] { margin-bottom: -0.5rem !important; }
[data-testid="stExpander"] { background-color: transparent !important; border: none !important; margin-top: -0.5rem !important; }
[data-testid="stExpander"] details { background-color: transparent !important; border: none !important; }
[data-testid="stExpander"] summary { font-size: 0.65rem !important; color: #86868b !important; font-family: 'JetBrains Mono', monospace !important; padding: 0 !important; background-color: transparent !important; }
[data-testid="stExpander"] summary span { font-size: 0.65rem !important; color: #86868b !important; background-color: transparent !important; }
[data-testid="stExpander"] summary svg { width: 0.65rem !important; height: 0.65rem !important; fill: #86868b !important; }
[data-testid="stExpander"] summary:hover, [data-testid="stExpander"] summary:hover span { color: #6ba3d6 !important; }
[data-testid="stExpander"] summary:hover svg { fill: #6ba3d6 !important; }
[data-testid="stExpander"] summary:focus, [data-testid="stExpander"] summary:active,
[data-testid="stExpander"] summary:focus span, [data-testid="stExpander"] summary:active span {
    color: #86868b !important; background-color: transparent !important; outline: none !important; box-shadow: none !important;
}
[data-testid="stExpander"] [data-testid="stExpanderDetails"] { background-color: transparent !important; border: none !important; padding: 0 0 0 0.5rem !important; }
::-webkit-scrollbar { display: none; }
* { -ms-overflow-style: none; scrollbar-width: none; }
code.red-badge { color: #c43e3e !important; }</style>
"""

# Theme toggle — persisted in session state
if "theme" not in st.session_state:
    st.session_state.theme = "clean"

st.markdown(PIPBOY_CSS if st.session_state.theme == "pipboy" else CLEAN_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    title_col, theme_col = st.columns([3, 1])
    with title_col:
        st.markdown("### > LEADRET")
    with theme_col:
        theme_icon = "☀️" if st.session_state.theme == "pipboy" else "🌙"
        if st.button(theme_icon, key="theme_toggle"):
            st.session_state.theme = "clean" if st.session_state.theme == "pipboy" else "pipboy"
            st.rerun()
    st.caption("V2.0 // LLM-DRIVEN RESEARCH")

    # Campaign selector (includes Custom Campaign option)
    st.markdown("**CAMPAIGN**")
    available_campaigns = list_campaigns()
    campaign_map = {}
    for fname in available_campaigns:
        try:
            c = load_campaign(fname)
            campaign_map[f"{c.name} ({fname})"] = (fname, c.name)
        except Exception:
            campaign_map[fname] = (fname, fname)

    CUSTOM_LABEL = "CUSTOM CAMPAIGN"
    options = list(campaign_map.keys()) + [CUSTOM_LABEL]

    selected_display = st.selectbox(
        "select campaign",
        options,
        key="campaign_select",
        label_visibility="collapsed",
    )

    is_custom = selected_display == CUSTOM_LABEL

    if is_custom:
        selected_campaign_file = None
        selected_campaign = "adhoc"
        adhoc_prompt = st.text_area(
            "research prompt",
            placeholder="> FIND ROBOTICS STARTUPS USING ROS2...",
            height=80,
            key="adhoc_prompt",
            label_visibility="collapsed",
        )
    else:
        selected_campaign_file, selected_campaign = campaign_map[selected_display]
        adhoc_prompt = ""

    # Research controls
    st.divider()
    st.markdown("**EXECUTE**")

    PROVIDERS = ["gemini", "perplexity", "grok"]
    PROVIDER_KEYS = {"gemini": GEMINI_API_KEY, "perplexity": PERPLEXITY_API_KEY, "grok": GROK_API_KEY}
    default_idx = PROVIDERS.index(RESEARCH_PROVIDER) if RESEARCH_PROVIDER in PROVIDERS else 0

    selected_provider = st.selectbox(
        "research provider",
        PROVIDERS,
        index=default_idx,
        format_func=lambda p: p.upper(),
        key="provider_select",
        label_visibility="collapsed",
    )

    if not PROVIDER_KEYS.get(selected_provider):
        st.warning(f"NO API KEY SET FOR {selected_provider.upper()}")

    python_exe = str(PROJECT_ROOT / "venv" / "Scripts" / "python.exe")
    pipeline_script = str(PROJECT_ROOT / "run_pipeline.py")

    def _run_research(args: list[str], label: str = "Research", timeout: int = 600):
        status_text = st.empty()
        progress_bar = st.progress(0)
        output_box = st.empty()

        # Run subprocess in thread so we can animate the progress bar
        result_holder = {"result": None, "error": None}

        def _worker():
            try:
                result_holder["result"] = subprocess.run(
                    [python_exe, pipeline_script] + args,
                    capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=timeout,
                )
            except subprocess.TimeoutExpired:
                result_holder["error"] = "timeout"
            except Exception as e:
                result_holder["error"] = str(e)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

        # Animate progress while waiting
        phases = [
            (0.15, "INITIALIZING"),
            (0.35, "SEARCHING WEB"),
            (0.60, "EXTRACTING LEADS"),
            (0.80, "PROCESSING RESULTS"),
            (0.90, "SAVING TO DATABASE"),
        ]
        phase_idx = 0
        progress = 0.0
        start_time = time.time()

        while thread.is_alive():
            elapsed = time.time() - start_time
            # Advance through phases based on time (spread across ~60s)
            if phase_idx < len(phases):
                target_pct, phase_label = phases[phase_idx]
                phase_time = target_pct * 60  # rough timing
                if elapsed > phase_time:
                    phase_idx += 1
                status_text.markdown(f"**[{phase_label}...]**")
            else:
                status_text.markdown("**[FINALIZING...]**")

            # Smooth progress: asymptotically approach 95%
            progress = min(0.95, 1.0 - 1.0 / (1.0 + elapsed / 30.0))
            progress_bar.progress(progress)
            time.sleep(0.3)

        thread.join()

        if result_holder["error"] == "timeout":
            progress_bar.progress(1.0)
            status_text.empty()
            st.error(f"[TIMEOUT] {label} EXCEEDED {timeout}S")
            return
        elif result_holder["error"]:
            progress_bar.progress(1.0)
            status_text.empty()
            st.error(f"[ERROR] {result_holder['error']}")
            return

        result = result_holder["result"]
        progress_bar.progress(1.0)

        if result.returncode == 0:
            status_text.markdown("**[COMPLETE]**")
            time.sleep(0.5)
            status_text.empty()
            progress_bar.empty()
            if result.stdout:
                lines = result.stdout.strip().splitlines()
                output_box.code("\n".join(lines[-8:]), language="text")
            time.sleep(1.5)
            st.rerun()
        else:
            status_text.markdown("**[FAILED]**")
            log = ""
            if result.stdout:
                log += result.stdout[-2000:]
            if result.stderr:
                log += "\n--- STDERR ---\n" + result.stderr[-1000:]
            output_box.code(log if log.strip() else "NO OUTPUT", language="text")

    provider_args = ["--provider", selected_provider]
    has_key = bool(PROVIDER_KEYS.get(selected_provider))

    if is_custom:
        if st.button("EXECUTE", use_container_width=True, type="primary", disabled=not adhoc_prompt.strip() or not has_key):
            _run_research(["--prompt", adhoc_prompt.strip()] + provider_args, label="CUSTOM RESEARCH")
    else:
        if st.button("EXECUTE", use_container_width=True, type="primary", disabled=not selected_campaign_file or not has_key):
            _run_research(["--campaign", selected_campaign_file] + provider_args, label="CAMPAIGN RESEARCH")

    st.divider()

    # Blocked companies
    st.markdown("**BLOCKLIST**")
    blocked_list = get_blocked_companies()
    if blocked_list:
        for bc in blocked_list:
            bc_col1, bc_col2 = st.columns([3, 1])
            with bc_col1:
                st.caption(f"~ {bc['company_name']}")
            with bc_col2:
                if st.button("x", key=f"unblock_{bc['company_name']}"):
                    unblock_company(bc["company_name"])
                    st.rerun()
    else:
        st.caption("empty")

# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------
campaign_filter = selected_campaign or ""

st.markdown("# > LEADRET")
if selected_campaign:
    st.caption(f"CAMPAIGN: {selected_campaign.upper()}")

# Stats — single query for all counts
conn = get_connection()
try:
    _where = "WHERE campaign=?" if campaign_filter else "WHERE 1=1"
    _params = (campaign_filter,) if campaign_filter else ()
    row = conn.execute(f"""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN user_rating IS NOT NULL THEN 1 ELSE 0 END) as rated,
            SUM(CASE WHEN user_rating IS NULL AND company_name NOT IN (SELECT company_name FROM blocked_companies) THEN 1 ELSE 0 END) as queue
        FROM leads {_where}
    """, _params).fetchone()
    total, r_cnt, q_cnt = row["total"], row["rated"], row["queue"]
finally:
    conn.close()

if total > 0:
    col1, col2, col3 = st.columns(3)
    col1.metric("TOTAL", total)
    col2.metric("RATED", r_cnt)
    col3.metric("QUEUE", q_cnt)
else:
    st.info("[ NO LEADS FOUND — RUN A CAMPAIGN OR AD-HOC QUERY ]")

st.divider()

# ---------------------------------------------------------------------------
# Helper: render a lead card
# ---------------------------------------------------------------------------
def _render_lead_card(lead, show_rating_buttons=True):
    """Render a single lead card."""
    with st.container():
        # Company name
        title = f"### {lead.company_name}"
        if lead.user_rating:
            title += f"  `{'★' * lead.user_rating}{'☆' * (5 - lead.user_rating)}`"
        st.markdown(title)

        # Tags line
        tags = []
        if lead.sector.value != "other":
            tags.append(lead.sector.value.replace("_", " ").title())
        if lead.company_type.value != "unknown":
            tags.append(lead.company_type.value.replace("_", " ").title())
        if lead.location:
            tags.append(lead.location)
        if tags:
            st.caption(" // ".join(tags))

        # Details
        detail_col1, detail_col2 = st.columns(2)

        with detail_col1:
            if lead.product_name:
                st.markdown(f"**product:** {lead.product_name}")
            if lead.tech_stack:
                badges = " ".join(f"`{t}`" for t in lead.tech_stack)
                st.markdown(f"**stack:** {badges}")
            if lead.funding_stage:
                st.markdown(f"**funding:** {lead.funding_stage}")

        with detail_col2:
            if lead.jetson_confirmed:
                if lead.jetson_models:
                    badges = " ".join(f"`{m}`" for m in lead.jetson_models)
                    st.markdown(f"**jetson:** {badges}")
                else:
                    st.markdown(f"**jetson:** `CONFIRMED`")
                if lead.jetson_usage:
                    st.markdown(f"**usage:** {lead.jetson_usage}")
            else:
                st.markdown("**jetson:** <code class='red-badge'>Unknown</code>", unsafe_allow_html=True)
            if lead.website_url:
                web_display = lead.website_url if len(lead.website_url) <= 40 else lead.website_url[:40] + "..."
                st.markdown(f"**web:** [{web_display}]({lead.website_url})")
                if lead.source_url:
                    with st.expander("SOURCE", expanded=False):
                        src_display = lead.source_url if len(lead.source_url) <= 50 else lead.source_url[:50] + "..."
                        st.markdown(f"[{src_display}]({lead.source_url})")
            else:
                new_web = st.text_input(
                    "web url",
                    key=f"web_{lead.id}",
                    placeholder="> MANUAL REVIEW — ENTER WEB URL...",
                    label_visibility="collapsed",
                )
                if new_web and new_web.startswith("http"):
                    update_lead(lead.id, website_url=new_web.strip())
                    st.rerun()

        if lead.summary:
            st.markdown(f"*{lead.summary}*")

        # Star rating + Delete/Block
        if show_rating_buttons:
            is_dark = st.session_state.theme == "pipboy"
            rate_col, spacer, del_col, block_col = st.columns([4, 8, 2, 2])
            with rate_col:
                star_bg = "#0a0e14" if is_dark else "#f5f5f7"
                rating = st_star_rating(
                    label="",
                    maxValue=5,
                    defaultValue=0,
                    size=24,
                    dark_theme=is_dark,
                    customCSS=f"div, header {{background-color: {star_bg} !important; border: none !important; box-shadow: none !important; margin: 0 !important; padding: 0 !important;}} body {{background-color: {star_bg} !important; overflow: visible !important;}} .stars-container, .star-wrapper {{overflow: visible !important;}} svg {{overflow: visible !important;}}",
                    key=f"star_{lead.id}",
                )
                if rating and rating > 0:
                    set_rating(lead.id, rating)
                    st.rerun()
            with del_col:
                if st.button("DELETE", key=f"del_{lead.id}"):
                    delete_lead(lead.id)
                    st.rerun()
            with block_col:
                if st.button("BLOCK", key=f"block_{lead.id}"):
                    block_company(lead.company_name, reason="Blocked from dashboard")
                    st.rerun()
        else:
            bq_col, spacer, sf_col = st.columns([3, 7, 3])
            with bq_col:
                if st.button("BACK TO QUEUE", key=f"bq_{lead.id}"):
                    update_lead(lead.id, user_rating=None)
                    st.rerun()
            with sf_col:
                st.button("PUSH TO SALESFORCE", key=f"sf_{lead.id}")

        st.divider()


# ---------------------------------------------------------------------------
# Tabs: Queue / Rated (custom implementation to preserve tab on rerun)
# ---------------------------------------------------------------------------
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "queue"

tab_q, tab_r = st.columns(2)
with tab_q:
    if st.button(f"> QUEUE [{q_cnt}]", use_container_width=True,
                 type="primary" if st.session_state.active_tab == "queue" else "secondary"):
        st.session_state.active_tab = "queue"
        st.rerun()
with tab_r:
    if st.button(f"> RATED [{r_cnt}]", use_container_width=True,
                 type="primary" if st.session_state.active_tab == "rated" else "secondary"):
        st.session_state.active_tab = "rated"
        st.rerun()

if st.session_state.active_tab == "queue":
    queue_leads = get_feed(campaign_filter, limit=50)
    if not queue_leads:
        st.info("[ QUEUE EMPTY — RUN RESEARCH OR ALL LEADS RATED ]")
    else:
        for lead in queue_leads:
            _render_lead_card(lead, show_rating_buttons=True)
else:
    rated_leads = get_rated_leads(campaign_filter)
    if rated_leads:
        for lead in rated_leads:
            _render_lead_card(lead, show_rating_buttons=False)
    else:
        st.info("[ NO RATED LEADS YET ]")

