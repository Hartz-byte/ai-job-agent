# AI Job Agent

An end-to-end, scriptable job search and application assistant. It:
- Searches multiple providers (LinkedIn, Indeed, Wellfound, Internshala).
- Stores results in SQLite.
- Tailors resume and cover letters per job.
- Optionally simulates application steps.
- Ships with a Streamlit dashboard to monitor logs and browse results.

Key entry points:
- Backend pipeline: `src/main.py`
- Dashboard UI: `streamlit_app.py`

## Features
- __Multi-provider search__: See `src/providers/` for `indeed.py`, `wellfound.py`, `internshala.py`, `linkedin.py`.
- __Live results storage__: SQLite via `src/storage/db.py`, models in `src/storage/models.py`.
- __Document tailoring__: LLM-assisted tailoring in `src/generators/tailor.py` with prompts in `src/llm/prompts.py`.
- __Resume parsing__: `src/parsers/resume_parser.py` supports PDF/DOCX.
- __Configurable preferences__: `src/preferences.py` and `.env` via `src/config.py`.
- __Streamlit dashboard__: `streamlit_app.py` shows live logs, results, and controls.
- __Logging__: Logs written to `output/logs/agent.log` and `output/logs/linkedin.log`.
- __Rate limiting & utilities__: See `src/utils/`.

## Project Structure
```
.
├─ src/
│  ├─ main.py                   # Orchestrates parse → search → tailor → apply
│  ├─ config.py                 # Loads .env into strongly-typed cfg
│  ├─ preferences.py            # Defaults for keywords/locations
│  ├─ providers/                # indeed, wellfound, internshala, linkedin
│  ├─ parsers/                  # resume & job parsers
│  ├─ generators/               # tailoring logic & Jinja templates
│  ├─ apply/                    # application logic
│  ├─ storage/                  # SQLite db + models
│  └─ utils/                    # logging, browser fetch, rate limit, etc.
├─ streamlit_app.py             # UI dashboard
├─ data/                        # resume and cover letter base templates
├─ output/
│  ├─ logs/                     # runtime logs
│  └─ tailored/                 # tailored docx outputs
├─ requirements.txt
└─ scripts/setup_playwright.sh  # Playwright setup helper
```

## Requirements
- Python 3.10+
- WSL/Unix or Windows (WSL recommended for Playwright)
- Chrome/Chromium for some scraping scenarios
- Optional: GPU for local LLMs

## Quick Start

1) Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate   # Windows WSL: source venv/bin/activate
pip install -r requirements.txt
```

2) Install Playwright browsers (needed by `utils.browser_fetch.fetch_html()` used by `src/providers/linkedin.py`):
```bash
python -m playwright install --with-deps
# or
bash scripts/setup_playwright.sh
```

3) Prepare data files:
- Put your resume at `data/resume.docx` (or `.pdf`) and ensure `RESUME_PATH` matches in `.env`.
- Base cover letter template exists at `data/cover_letter_base.docx`.

4) Configure environment:
- Create `.env` at project root. See the template below.

5) Run the backend pipeline:
```bash
python -m src.main
# or
python src/main.py
```

6) Run the dashboard:
```bash
streamlit run streamlit_app.py
```

## .env Template

The app loads configuration via `src/config.py` using `dotenv`. Defaults are sensible, but you can override:

```
# LLM
LLM_MODE=local                # local | openai
LLAMA_MODEL_PATH=./models/mistral-7b-instruct-v0.2.Q4_K_M.gguf
LLAMA_CTX=4096
LLAMA_N_THREADS=6
LLAMA_N_GPU_LAYERS=20

# OpenAI (if LLM_MODE=openai)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Documents
RESUME_PATH=./data/resume.docx
RESUME_TEMPLATE_PATH=
COVER_LETTER_BASE_PATH=./data/cover_letter_base.docx

# Search prefs
COUNTRIES=India
CITIES=Gurugram, Delhi, Noida, Bangalore, Pune, Hyderabad
REMOTE_OK=true
REMOTE_GLOBAL_OK=true
KEYWORDS=machine learning,ml engineer

# Providers on/off
ENABLE_LINKEDIN=true
ENABLE_INDEED=true
ENABLE_WELLFOUND=true
ENABLE_INTERNSHALA=true

# Apply behaviors
APPLY_LINKEDIN_EASY_APPLY=true
APPLY_INTERNSHALA=true
APPLY_WELLFOUND=true
APPLY_INDEED=false

# Rate limiting
REQUESTS_PER_MIN=16

# SQLite
DB_PATH=./agent.db

# LinkedIn credentials (required for LinkedIn scraping/login flow)
LINKEDIN_EMAIL=you@example.com
LINKEDIN_PASSWORD=your-password
```

Notes:
- `RESUME_PATH` supports `.pdf` or `.docx` (`src/parsers/resume_parser.py`).
- If `DB_PATH` is not set, it defaults to `./agent.db`.

## How It Works

- `src/main.py` orchestrates:
  - `parse_resume(cfg.resume_path)` from `src/parsers/resume_parser.py`.
  - `gather_jobs()` queries enabled providers: `indeed.py`, `wellfound.py`, `internshala.py`, `linkedin.py`.
  - Jobs are upserted into SQLite via `src/storage/db.py` (`upsert_job()`).
  - `process_jobs()` tailors resume and cover letter for each job via `src/generators/tailor.py`, then calls `apply()` in `src/apply/applicant.py`.
- The Streamlit UI (`streamlit_app.py`) provides:
  - Live logs (auto-refresh using `streamlit-extras`): `output/logs/agent.log`, `output/logs/linkedin.log`.
  - Results tab showing rows directly from SQLite via `src/storage/db.py`.
  - Search controls to run a live search thread in the UI session.

## Logs

- Backend logs:
  - `output/logs/agent.log` (pipeline)
  - `output/logs/linkedin.log` (LinkedIn provider)
- UI logs auto-refresh using `st_autorefresh` from `streamlit-extras`. If not installed, the UI falls back gracefully with a note.

## Database

- SQLite file path controlled by `DB_PATH` (.env), default `./agent.db`.
- Tables auto-created if DB file is missing (`src/storage/db.py`).

Reset database for a fresh start:
- Option A (delete file; tables will be recreated):
```bash
rm -f ./agent.db
```
- Option B (truncate tables; keep file):
```bash
python - <<'PY'
import sys, sqlite3
sys.path.insert(0, './src')
from config import cfg
conn = sqlite3.connect(cfg.db_path)
with conn:
    conn.execute("DELETE FROM applications;")
    conn.execute("DELETE FROM jobs;")
conn.close()
print("Cleared tables: jobs, applications")
PY
```

## Tailoring

- Implemented in `src/generators/tailor.py`.
- Uses `src/llm/prompts.py` and either local LLM (`src/llm/local_llm.py`) or OpenAI, based on `LLM_MODE`.
- Outputs tailored `.docx` resume and cover letter to `output/tailored/`.
- Jinja base template for cover letters: `src/generators/cover_letter_template.jinja`.

## Providers

- See `src/providers/`. Each provider exposes a `search(query: str, locations: list[str]) -> Iterable[JobPost]`.
- `src/providers/linkedin.py` uses requests and Playwright-backed HTML fetching for resilience.
- LinkedIn requires `LINKEDIN_EMAIL` and `LINKEDIN_PASSWORD` in `.env`.

## Streamlit UI

Run:
```bash
streamlit run streamlit_app.py
```
- Sidebar controls to start/stop search threads and toggle data source (live session vs DB).
- Tabs:
  - Live Logs: tails logs with auto-refresh.
  - Results: shows latest jobs from DB or session.
  - About: quick help and links.

If `streamlit-extras` is missing, the UI still works; install it for auto-refresh:
```bash
pip install streamlit-extras
```

## Troubleshooting

- __ModuleNotFoundError__: Install missing deps and re-run:
  - `pip install -r requirements.txt`
  - For UI auto-refresh: `pip install streamlit-extras`
- __Playwright Errors__: Ensure browsers installed:
  - `python -m playwright install --with-deps`
- __LinkedIn Login Fails__:
  - Verify `LINKEDIN_EMAIL` and `LINKEDIN_PASSWORD` in `.env`.
  - Expect occasional 429s; provider includes backoff and parsing fallbacks.
- __No results in UI__:
  - Ensure providers enabled in `.env` or toggle in UI.
  - Check logs under `output/logs/`.
  - Confirm DB path in `.env` matches what you expect.

## Development

- Code style: standard Python, minimal external tooling.
- Add providers by implementing `search()` to yield `storage.models.JobPost`.
- Update prompts or local LLM config in `src/llm/`.

## Roadmap
- LinkedIn Easy Apply automation
- More providers and geo targeting
- Robust deduping/normalization across providers
- Advanced ranking and filtering
- Export to CSV/Notion
- Notification hooks

## License
MIT (or your preferred license). Update this section accordingly.

## Acknowledgements
- Streamlit ecosystem for the dashboard
- Playwright for robust fetching
- BeautifulSoup/lxml for parsing

---

If you want, I can also add badges, screenshots/gifs, and a minimal demo dataset to make the README even more compelling on GitHub.