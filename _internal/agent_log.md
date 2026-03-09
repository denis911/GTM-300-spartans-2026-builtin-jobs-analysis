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

## Checkpoint 1.2a: PDF Review & Scraper Refactoring
- **Issue**: Test run produced only 20 results (default limit) and "enqueueLinks limit of 0" warning.
- **Discovery**: User-provided "BuiltIn Jobs Scraper.pdf" revealed correct input keys: `results_wanted`, `startUrl` (singular), and `max_pages`.
- **Decision**: Refactored `00_run_apify.py` to loop through search URLs one-by-one to support both actors reliably.
- **Verification**: New test run with 1 URL/10 items succeeded with correct field mapping.

## [CHECKPOINT 1.3] — 2026-03-09 21:15
**Summary**: Completed full collection using the refactored loop and PDF-verified keys.
**Results**:
- Total Items: 829 unique (deduplicated from ~1400 raw across 6 URLs).
- Coverage: 100% on core job details.
- Cost: /usr/bin/bash.02 (well within free tier).
**Decisions**: Used `startUrl`, `results_wanted`, and `max_pages` as per PDF. The role-based URL provided high volume.
**Next**: Move to Stage 2 - LLM-driven cleaning and YAML export.
