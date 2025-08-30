import os
import sys
import threading
from datetime import datetime
from typing import List

# Ensure src/ is importable when running from project root
BASE_DIR = os.path.dirname(__file__)
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import streamlit as st  # noqa: E402
try:
    from streamlit_extras.st_autorefresh import st_autorefresh
except Exception:
    # Fallback: define a no-op if optional extra is not installed
    def st_autorefresh(interval: int = 1000, key: str | None = None, *args, **kwargs):
        """Lightweight auto-refresh using HTML meta-refresh as a fallback.

        interval: milliseconds between refreshes (rounded to >=1s for meta refresh)
        key: unused, kept for API compatibility
        """
        # Meta refresh supports seconds granularity; keep it >= 1s
        seconds = max(int(interval / 1000), 1)
        st.markdown(
            f"<meta http-equiv='refresh' content='{seconds}'>",
            unsafe_allow_html=True,
        )

from config import cfg  # noqa: E402
from preferences import get_preferences  # noqa: E402
from storage.models import JobPost  # noqa: E402
from providers import indeed as indeed_p  # noqa: E402
from providers import wellfound as wellfound_p  # noqa: E402
from providers import internshala as internshala_p  # noqa: E402
from providers import linkedin as linkedin_p  # noqa: E402
from utils.logger import get_logger  # noqa: E402
from storage.db import get_conn  # noqa: E402

logger = get_logger("ui")

LOG_FILES = [
    ("Agent", os.path.join("output", "logs", "agent.log")),
    ("LinkedIn", os.path.join("output", "logs", "linkedin.log")),
]


def _ensure_dirs():
    os.makedirs(os.path.join("output", "logs"), exist_ok=True)
    os.makedirs(os.path.join("output", "tailored"), exist_ok=True)


def _tail_file(path: str, max_lines: int = 200) -> List[str]:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        return lines[-max_lines:]
    except FileNotFoundError:
        return [f"[no log yet at {path}]"]
    except Exception as e:
        return [f"[log read error: {e}]"]


def _run_search_thread(keywords: List[str], locations: List[str], providers_flags: dict):
    """Search providers sequentially and store results in session_state."""
    jobs: List[JobPost] = []
    seen_ids = set()

    provider_list = []
    if providers_flags.get("indeed"):
        provider_list.append(("indeed", indeed_p.search))
    if providers_flags.get("wellfound"):
        provider_list.append(("wellfound", wellfound_p.search))
    if providers_flags.get("internshala"):
        provider_list.append(("internshala", internshala_p.search))
    if providers_flags.get("linkedin"):
        provider_list.append(("linkedin", linkedin_p.search))

    for kw in keywords:
        for name, fn in provider_list:
            try:
                logger.info(f"UI: Searching {name} for '{kw}'")
                for job in fn(kw, locations):
                    if job.job_id in seen_ids:
                        continue
                    seen_ids.add(job.job_id)
                    jobs.append(job)
                    # update streamlit state incrementally
                    st.session_state.jobs = jobs
                    st.session_state.last_update = datetime.now().isoformat(timespec='seconds')
            except Exception as e:
                logger.warning(f"UI provider {name} error: {e}")
    st.session_state.search_running = False


def main():
    _ensure_dirs()
    st.set_page_config(page_title="AI Job Agent", layout="wide")
    st.title("AI Job Agent Dashboard")
    st.caption("Search and monitor job aggregation in real time. Tailor/apply handled by backend pipeline.")

    if "jobs" not in st.session_state:
        st.session_state.jobs = []
    if "search_running" not in st.session_state:
        st.session_state.search_running = False
    if "last_update" not in st.session_state:
        st.session_state.last_update = ""

    with st.sidebar:
        st.header("Search Settings")
        prefs = get_preferences()
        kw_input = st.text_input("Keywords (comma-separated)", ", ".join(prefs.keywords))
        loc_input = st.text_input("Locations (comma-separated)", ", ".join(prefs.cities or ["India"]))

        st.subheader("Providers")
        p_indeed = st.checkbox("Indeed", value=cfg.enable_indeed)
        p_wellfound = st.checkbox("Wellfound", value=cfg.enable_wellfound)
        p_internshala = st.checkbox("Internshala", value=cfg.enable_internshala)
        p_linkedin = st.checkbox("LinkedIn", value=cfg.enable_linkedin)

        st.subheader("Controls")
        col_a, col_b = st.columns(2)
        with col_a:
            start = st.button("Start Search", disabled=st.session_state.search_running)
        with col_b:
            stop = st.button("Stop", disabled=not st.session_state.search_running)

        st.subheader("Results Source")
        show_db = st.checkbox("Show results from database (includes backend main.py)", value=True, help="If enabled, the Results tab will read from the SQLite jobs table so you can see jobs gathered by the backend pipeline.")
        st.session_state.show_db = show_db

        st.subheader("Live Logs Settings")
        auto_refresh_logs = st.checkbox("Auto-refresh logs (every 10s)", value=False, help="Turn ON for background monitoring; keep OFF while interacting to avoid page refresh.")
        st.session_state.auto_refresh_logs = auto_refresh_logs

        if start and not st.session_state.search_running:
            st.session_state.jobs = []
            st.session_state.search_running = True
            keywords = [k.strip() for k in kw_input.split(",") if k.strip()]
            locations = [loc.strip() for loc in loc_input.split(",") if loc.strip()]
            providers_flags = {
                "indeed": p_indeed,
                "wellfound": p_wellfound,
                "internshala": p_internshala,
                "linkedin": p_linkedin,
            }
            t = threading.Thread(target=_run_search_thread, args=(keywords, locations, providers_flags), daemon=True)
            t.start()
        if stop and st.session_state.search_running:
            # Cooperative stop: just flip the flag; providers iterate quickly
            st.session_state.search_running = False

    # Main layout
    tab_logs, tab_results, tab_about = st.tabs(["Live Logs", "Results", "About"]) 

    with tab_logs:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Agent Log**")
            agent_area = st.empty()
        with col2:
            st.markdown("**LinkedIn Log**")
            li_area = st.empty()

        # Auto-refresh only if user enabled it; otherwise provide manual refresh
        if st.session_state.get("auto_refresh_logs", False):
            st_autorefresh(interval=10000, key="logs_refresh")
        else:
            st.info("Auto-refresh is off. Click to refresh logs.")
            st.button("Refresh now", key="refresh_logs_now")
        agent_lines = _tail_file(LOG_FILES[0][1])
        li_lines = _tail_file(LOG_FILES[1][1])
        agent_area.code("".join(agent_lines), language="text")
        li_area.code("".join(li_lines), language="text")

    with tab_results:
        st.subheader("Found Jobs")
        st.caption(f"Last update: {st.session_state.last_update}")

        def _load_jobs_from_db(limit: int = 200):
            try:
                conn = get_conn()
                cur = conn.cursor()
                cur.execute("SELECT id, title, company, location, url, source, created_at FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,))
                rows = cur.fetchall()
                conn.close()
                return rows
            except Exception as e:
                st.warning(f"DB read failed: {e}")
                return []

        if st.session_state.get("show_db", True):
            rows = _load_jobs_from_db()
            st.write(f"Total (latest {len(rows)} from DB): {len(rows)}")
            for (jid, title, company, location, url, source, created_at) in rows:
                with st.container(border=True):
                    top = st.columns([3, 2, 2, 2, 1])
                    with top[0]:
                        st.markdown(f"**{title}**")
                    with top[1]:
                        st.text(company)
                    with top[2]:
                        st.text(location)
                    with top[3]:
                        st.text(source)
                    with top[4]:
                        st.link_button("Open", url or "#")
                    with st.expander("Meta"):
                        st.text(f"Job ID: {jid}")
                        st.text(f"Created: {created_at}")
        else:
            jobs = st.session_state.jobs or []
            st.write(f"Total (this UI session): {len(jobs)}")
            for j in jobs:
                with st.container(border=True):
                    top = st.columns([3, 2, 2, 2, 1])
                    with top[0]:
                        st.markdown(f"**{j.title}**")
                    with top[1]:
                        st.text(j.company)
                    with top[2]:
                        st.text(j.location)
                    with top[3]:
                        st.text(j.source)
                    with top[4]:
                        st.link_button("Open", j.url or "#")
                    with st.expander("About this job"):
                        st.write(j.description or "")

    with tab_about:
        st.markdown("""
        ### App Details
        - Shows real-time logs from `output/logs/agent.log` and `output/logs/linkedin.log`.
        - Searches selected providers sequentially using your input keywords and locations.
        - Results update live without restarting the app.
        - Backend tailoring and apply steps are not triggered from this UI.

        #### Tips
        - Configure preferences and providers in `src/preferences.py` and `src/config.py`.
        - Ensure `.env` has any credentials needed (e.g., LinkedIn if required).
        - Anchors in resume templates supported: `{{SUMMARY}}`, `{{BULLETS}}`, `{{SKILLS}}` or `[TAILOR_*]` variants.
        """)


if __name__ == "__main__":
    main()
