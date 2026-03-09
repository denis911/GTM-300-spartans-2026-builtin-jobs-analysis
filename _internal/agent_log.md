# Agent Decision Log

---
## [CHECKPOINT 0.1] — 2026-03-09 10:25
**Summary:** Initialized project directory structure, updated `pyproject.toml` with final dependencies, and set up `agent_log.md`. Verified environment variables (APIFY_API_TOKEN, OPENAI_API_KEY) and `uv` environment.
**Decisions:** Adopted the standard 5-city coverage from `TASK.md`. Created `_internal/charts` and `data_*` directories ahead of time for cleanliness. Updated `.gitignore` with project-specific exclusions.
**Issues:** None.
---
---
## [CHECKPOINT 1.1] — 2026-03-09 20:01
**Summary:** Created _internal/apify_input.json with target GTM search URLs and _internal/00_run_apify.py for orchestration.
**Decisions:** Included 6 search URLs (covering NY, CA, USA Remote, GBR, DEU, and a specific GTM role) as per the instruction template. Updated paths in the script to use absolute paths relative to the script location for reliability.
**Issues:** None.
---

## Checkpoint 1.2: Test Scrape Completed
- **Status**: Success
- **Actor**: Fallback actor `shahidirfan/builtin-jobs-scraper` used automatically (Primary actor requires subscription/proxy access).
- **Fixes**: Updated `00_run_apify.py` with normalization logic for `description_text`, `date_posted`, and `salary_json_*` fields.
- **Coverage**: 100% for Core fields (Title, Company, Location, Description, URL, PostedDate).
- **Cost**: 0.003 CU used for test run. Projected cost for 350 items: ~/usr/bin/bash.02 (Free tier sufficient).
