# TASK.md — GTM Engineer Job Market Analysis
## Project: Scrape & Analyze ~300 GTM Engineer Job Postings from Builtin.com

> **Reference project:** [alexeygrigorev/ai-engineering-field-guide/job-market](https://github.com/alexeygrigorev/ai-engineering-field-guide/tree/main/job-market)
> This project replicates that methodology for the GTM engineering niche.

---

## ⚠️ AGENT OPERATING RULES — READ FIRST, FOLLOW ALWAYS

1. **One checkpoint at a time.** Complete it fully, then stop. Never chain checkpoints together.
2. **At every `🛑 STOP` marker:** write a concise summary of what was done, list any decisions made or issues found, then **wait for explicit human approval** before continuing.
3. **Never auto-proceed** — even if the next step seems obvious or trivial.
4. **Log every checkpoint** by appending an entry to `_internal/agent_log.md` before stopping. Format: `## [CHECKPOINT X.Y] — [date/time]\n[summary]\n[decisions]\n[issues]`
5. **Flag ambiguity** rather than guessing silently. If something is unclear, state your assumption in the log and STOP summary so the human can correct it.
6. **No speculative work.** Do not write code for a future checkpoint while waiting on the current one.

---

## Project Overview

Collect ~300 GTM (Go-To-Market) Engineer job descriptions from Builtin.com, structured by city, clean and normalize the data with an LLM extraction step, run a comprehensive Jupyter notebook analysis, and produce GitHub-ready documentation.

### Target Cities
| City | Rationale |
|---|---|
| New York, NY | Largest US GTM hub; enterprise SaaS density |
| San Francisco Bay Area, CA | Startup GTM epicenter |
| London, UK | Top European GTM market |
| Berlin, Germany | Europe's fastest-growing B2B SaaS scene |
| Austin, TX | SaaS corridor; Dell, Indeed, Salesforce tower; fast-growing mid-market GTM scene |

---

## Final Deliverables

```
gtm-job-market/
├── data_raw/                    # One raw YAML per job (post-dedup)
├── data_structured/             # One normalized YAML per job (LLM-extracted)
├── _internal/
│   ├── apify_input.json         # Apify actor run configuration
│   ├── apify_raw_export.json    # Raw Apify dataset output
│   ├── apify_raw_export.csv     # Same, CSV format
│   ├── 00_run_apify.py          # Phase 1: scraper trigger script
│   ├── 01_deduplicate.py        # Phase 2: dedup + raw YAML writer
│   ├── 02_structure.py          # Phase 3: LLM structuring script
│   ├── dedup_report.csv         # Deduplication funnel statistics
│   ├── charts/                  # PNG exports from notebook (≥10 files)
│   └── agent_log.md             # Agent decision log (append-only)
├── analysis.ipynb               # Full analysis notebook
├── README.md                    # GitHub project documentation
├── pyproject.toml               # Python dependency manifest
├── .python-version              # Python version pin (3.12)
└── .gitignore
```

---

## Phases & Checkpoints

---

### PHASE 0 — Environment Setup - mostly done manually by user, no need to run - agent provides only instructions and updates README.md while keeping original texts. Agent may create directories if needed.

#### ✅ Checkpoint 0.1 — Project skeleton & dependencies

**Tasks:**
- Create all directories listed above (including `_internal/charts/`)
- Create `pyproject.toml` (update content like in INSTRUCTIONS.md §`pyproject.toml`)
- Create `.python-version` containing `3.13` - done by user
- Create `.gitignore` (update content like in INSTRUCTIONS.md §`.gitignore`) - done by user
- Create `_internal/agent_log.md` with header + first entry
- Run `uv sync` and confirm clean install — capture output
- Print masked env vars: `APIFY_API_TOKEN` (first 6 chars + `****`) and `OPENAI_API_KEY` (first 6 chars + `****`) — confirm both are set

**🛑 STOP 0.1**
Output: full directory tree, install output summary (any errors?), masked env var confirmation.
Human checks: correct Python version? All dirs created? Both API keys accessible?

---

### PHASE 1 — Data Collection

#### ✅ Checkpoint 1.1 — Apify actor config (files only, no run)

**Tasks:**
- Write `_internal/apify_input.json` with the 5-city search URLs and `maxItems: 10` (test mode — do NOT change to 350 yet)
- Write `_internal/00_run_apify.py` (full script per INSTRUCTIONS.md §1.2)
- Do NOT execute anything

**🛑 STOP 1.1**
Output: print contents of `apify_input.json` in full. Show first 30 lines of `00_run_apify.py`.
Human checks: are search URLs correct? Is the actor ID right? Are all 5 cities covered?

---

#### ✅ Checkpoint 1.2 — Test scrape (10 items, 1 URL only)

**Purpose:** Validate the actor works and estimate cost before spending real credits.

**Tasks:**
- Temporarily set `maxItems: 10` and use only the **first search URL** in the input
- Run `python _internal/00_run_apify.py`
- Print 2–3 sample records showing: `title`, `company`, `location`, `skills` (array), `description` (first 200 chars), `salary`, `url`
- From the Apify run metrics, record: total compute units used, actual cost in $
- Extrapolate estimated cost for 350 items across all URLs
- Assess field coverage: which fields are consistently populated vs. missing?

**🛑 STOP 1.2**
Output: 2–3 sample records, field coverage table, estimated cost for full run.
Human decides: proceed with this actor? Switch to a different actor? Accept missing fields?

---

#### ✅ Checkpoint 1.3 — Full scrape (all cities, ~350 items)

**Tasks:**
- Restore `apify_input.json` to all 5 city URLs with `maxItems: 350`
- Run `python _internal/00_run_apify.py`
- Save results to `_internal/apify_raw_export.json` and `_internal/apify_raw_export.csv`
- Print: total records retrieved, Apify dataset ID (for reference), actual run cost
- Quick city breakdown: count records where `location` mentions each target city (approximate)

**🛑 STOP 1.3**
Output: total records, city distribution table, run cost, any actor errors or partial failures.
Human checks: enough records? Any cities with zero results? OK to proceed to dedup?

---

### PHASE 2 — Deduplication & Raw YAML

#### ✅ Checkpoint 2.1 — Write dedup script (no run)

**Tasks:**
- Write `_internal/01_deduplicate.py` (full implementation per INSTRUCTIONS.md §2)
- Do NOT run

**🛑 STOP 2.1**
Output: print the GTM keyword filter list and fuzzy dedup threshold as they appear in the script.
Human checks: any missing keywords? Is the 90% fuzzy threshold right? Add/remove anything?

---

#### ✅ Checkpoint 2.2 — Run dedup & inspect results

**Tasks:**
- Run `python _internal/01_deduplicate.py`
- Print the full dedup funnel from `_internal/dedup_report.csv`
- Print 3 sample raw YAML files (show complete content)
- Print 3 examples of records that were **removed** (with removal reason: url-dup, non-GTM, fuzzy-dup) so the human can sanity-check the filter

**🛑 STOP 2.2**
Output: dedup funnel table, 3 kept samples, 3 removed samples with reasons.
Human checks: did the filter correctly exclude non-GTM roles? Did it keep all valid GTM variants? Final count acceptable (target: ≥ 280)?

---

### PHASE 3 — LLM Structuring

#### ✅ Checkpoint 3.1 — Write structuring script (no run)

**Tasks:**
- Write `_internal/02_structure.py` (full implementation per INSTRUCTIONS.md §3)
- Do NOT run

**🛑 STOP 3.1**
Output: print the **full Claude extraction prompt** as it will be sent. Print the `job_type` category definitions.
Human checks: is the prompt clear? Are the categories right for GTM? Should any tool categories be added/renamed?

---

#### ✅ Checkpoint 3.2 — Pilot structuring (5 jobs)

**Tasks:**
- Run structuring on `data_raw/0001.yaml` through `data_raw/0005.yaml` only
- Print all 5 resulting structured YAMLs in full
- Note any JSON parse errors, missing fields, or suspicious classifications

**🛑 STOP 3.2**
Output: 5 structured YAML outputs. Flag any issues with job_type classification, tool extraction, or prompt failures.
Human checks: are the classifications sensible? Is the tool extraction accurate? Approve prompt before the full ~280-call API run.

---

#### ✅ Checkpoint 3.3 — Full structuring run

**Tasks:**
- Run `python _internal/02_structure.py --resume` (skips already-processed files)
- Monitor for errors — if error rate exceeds 10%, stop and report immediately
- When complete: print structured file count, error count, list of failed files

**🛑 STOP 3.3**
Output: final structured count, errors, estimated OpenAI API cost (input+output tokens × GPT-4o mini model price).
Human checks: acceptable error rate? Any systematic failures (e.g., specific fields always missing)?

---

### PHASE 4 — Validation

#### ✅ Checkpoint 4.1 — Schema validation & completeness check

**Tasks:**
- Run the validation script from INSTRUCTIONS.md §Validation
- Output a table showing: total files, files missing each required field, files with empty `description`, files with empty `tech_stack`
- List any individual files that fail multiple validations (candidates for manual inspection or re-run)

**🛑 STOP 4.1**
Output: validation results table, list of problematic files.
Human decides: fix specific files? Re-run structuring on failures? Accept as-is? Proceed?

---

### PHASE 5 — Jupyter Notebook

#### ✅ Checkpoint 5.1 — Notebook skeleton + data loading

**Tasks:**
- Create `analysis.ipynb` with all 10 section headers as markdown cells + stub code cells
- Implement **Section 0 only** (setup and data loading)
- Run Section 0, confirm it loads data without errors
- Print: record count, DataFrame column list, dtypes, `df.head(3)`

**🛑 STOP 5.1**
Output: DataFrame shape, columns, head(3). Confirm the 280+ records are loading correctly.

---

#### ✅ Checkpoint 5.2 — Sections 1, 2, 3 (Overview · Job Types · Compensation)

**Tasks:**
- Implement and run Sections 1 (Dataset Overview), 2 (Job Type Distribution), 3 (Compensation Analysis)
- Save charts: `01_top_companies.png`, `02_job_type_distribution.png`, `03_compensation_analysis.png`
- Print summary stats: top 5 companies, job type %, median salary by level

**🛑 STOP 5.2**
Output: printed stats, chart file confirmation. Human reviews findings for accuracy and chart quality.

---

#### ✅ Checkpoint 5.3 — Sections 4, 5, 6 (Location · Tech Stack · Languages)

**Tasks:**
- Implement and run Sections 4 (Location & Remote), 5 (Tech Stack), 6 (Languages)
- Save charts: `04_location_remote.png`, `05_top_tools.png`, `06_tool_categories.png`, `07_tool_cooccurrence.png`, `08_languages.png`
- Print: remote % breakdown, top 10 tools, top 5 languages

**🛑 STOP 5.3**
Output: printed stats, chart list. Human checks if tool categorization looks reasonable, remote % makes sense.

---

### PHASE 5.R — Visual Refinements

#### [x] Checkpoint 5.R — Replace charts with tables (Sec 1-2)

**Tasks:**
- [x] Modify Section 1 to show a table for Top 10 Companies.
- [x] Modify Section 2 to show a table for Job Type Distribution.
- [x] Confirm table readability and data accuracy.
- [x] Update README.md to reflect visual refinements.

**🛑 STOP 5.R**
Output: Updated Sections 1 & 2 in the notebook.
Human checks: Are the tables formatted correctly? Is the information density improved?

---

#### ✅ Checkpoint 5.4 — Sections 7, 8, 9, 10 (Experience · Company Size · Temporal · Findings)

**Tasks:**
- Implement and run Sections 7 (Experience & Seniority), 8 (Company Size), 9 (Temporal Trends), 10 (Key Findings)
- Section 10 **must use computed variables** — no hardcoded numbers
- Run full notebook end-to-end: `jupyter nbconvert --to notebook --execute --inplace analysis.ipynb`
- Print: execution status, any warnings or errors per cell

**🛑 STOP 5.4**
Output: full notebook execution result, complete chart list (count), any errors.

---

### PHASE 6 — Documentation & Cleanup

#### ✅ Checkpoint 6.1 — README draft

**Tasks:**
- Write `README.md` using template from INSTRUCTIONS.md §README
- Pull all statistics from computed values — do not approximate or guess
- Include: dataset summary, top findings, data format example, methodology, reproduction commands

**🛑 STOP 6.1**
Output: print the full README.md content.
Human reviews for accuracy, tone, and completeness before finalizing.

---

#### ✅ Checkpoint 6.2 — Final repo check

**Tasks:**
- Verify `.gitignore` correctly excludes sensitive/large files (see INSTRUCTIONS.md §`.gitignore`)
- Confirm `data_raw/` and `data_structured/` are NOT gitignored
- Run the notebook one final time cleanly
- Print final file counts: `data_raw/` count, `data_structured/` count, `_internal/charts/` count

**🛑 STOP 6.2 — PROJECT COMPLETE**
Output: final directory tree, file counts, gitignore contents. Project is ready for human final review and `git push`.

---

## Success Criteria Checklist

- [x] ≥ 280 unique GTM engineer records in `data_structured/` (Result: 310)
- [x] All 5 target cities represented in the dataset
- [x] Zero duplicate URLs in `data_structured/`
- [x] All records have: `title`, `company`, `job_type`, `tech_stack`, `url`
- [x] Notebook executes end-to-end without errors
- [x] High-density tables or charts for all key sections (≥ 6 charts + 2 tables)
- [x] README stats match notebook output
- [x] `agent_log.md` has an entry for every completed checkpoint
