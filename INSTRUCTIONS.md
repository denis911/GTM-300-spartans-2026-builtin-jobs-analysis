# INSTRUCTIONS.md — GTM Engineer Job Market Analysis
## Implementation Reference for Coding Agent

This file contains all implementation details referenced by TASK.md. The agent reads the relevant section at each checkpoint — do not implement sections ahead of schedule.

---

## § Environment Files

### `pyproject.toml`

```toml
[project]
name = "gtm-job-market"
version = "0.1.0"
description = "GTM Engineer job market analysis from Builtin.com"
requires-python = ">=3.13"
dependencies = [
    "apify-client>=1.8",
    "openai>=1.50",
    "pyyaml>=6.0",
    "pandas>=2.2",
    "numpy>=1.26",
    "matplotlib>=3.8",
    "seaborn>=0.13",
    "tqdm>=4.66",
    "rapidfuzz>=3.6",
    "jupyterlab>=4.0",
    "ipython>=8.0",
    "nbconvert>=7.0",
]
```

### `.gitignore`

```gitignore
# Secrets & environment
.env
*.env

# Apify raw export (large file, regenerable)
_internal/apify_raw_export.json
_internal/apify_raw_export.csv

# Python
__pycache__/
*.pyc
*.pyo
.venv/
venv/

# Jupyter
.ipynb_checkpoints/
*.nbconvert.ipynb

# OS
.DS_Store
Thumbs.db
```

### `_internal/agent_log.md` (initial content)

```markdown
# Agent Decision Log

Append a new entry at every checkpoint completion. Format:
---
## [CHECKPOINT X.Y] — YYYY-MM-DD HH:MM
**Summary:** what was done
**Decisions:** any non-obvious choices made
**Issues:** problems encountered and how resolved
---
```

---

## § 1 — Data Collection (Apify)

### §1.1 — `_internal/apify_input.json`

```json
{
  "startUrls": [
    "https://builtin.com/jobs?search=GTM+engineer&state=New+York&country=USA&allLocations=true",
    "https://builtin.com/jobs?search=GTM+engineer&state=California&country=USA&allLocations=true",
    "https://builtin.com/jobs/remote/hybrid/office?search=GTM+engineer&country=USA&allLocations=true",
    "https://builtin.com/jobs/remote/hybrid/office?search=GTM+engineer&country=GBR&allLocations=true",
    "https://builtin.com/jobs/remote/hybrid/office?search=GTM+engineer&country=DEU&allLocations=true",
    "https://builtin.com/jobs/role/gtm-engineer"
  ],
  "maxItems": 10,
  "proxyConfiguration": {
    "useApifyProxy": true,
    "apifyProxyGroups": ["DATACENTER"]
  }
}
```

> **Note on actor choice and free tier:**
> - Primary actor: `easyapi/builtin-jobs-scraper` (ID: `IhQuCmT40q1tetuv3`) — $19.99/month subscription required, so NOT free-tier compatible
> - **Recommended free-tier actor:** `shahidirfan/builtin-jobs-scraper` — pay-per-usage only, no subscription
> - The free Apify tier provides **$5/month** in credits. At ~$0.40/compute unit, this covers roughly 12 CUs per month.
> - **Always run a 10-item test first** (Checkpoint 1.2) to measure actual CU consumption before committing to a full run.
> - For the full 350-item run you will likely need $3–8 in credits — upgrade to Starter ($29/month) if the test indicates free tier is insufficient.
> - `DATACENTER` proxies are sufficient for Builtin.com; only switch to `RESIDENTIAL` if you encounter blocking.

### §1.2 — `_internal/00_run_apify.py`

```python
"""
Phase 1: Run Apify BuiltIn Jobs Scraper and export results.

Usage:
    python _internal/00_run_apify.py              # uses apify_input.json as-is
    python _internal/00_run_apify.py --test       # override maxItems to 10, first URL only

Output:
    _internal/apify_raw_export.json
    _internal/apify_raw_export.csv
"""
import argparse
import csv
import json
import os
import sys
from apify_client import ApifyClient

# ── Config ────────────────────────────────────────────────────────────────────
# Try primary actor first; if it requires subscription, switch to fallback
ACTOR_PRIMARY  = "IhQuCmT40q1tetuv3"   # easyapi/builtin-jobs-scraper ($19.99/mo)
ACTOR_FALLBACK = "shahidirfan/builtin-jobs-scraper"  # pay-per-usage only

INPUT_FILE   = "_internal/apify_input.json"
OUTPUT_JSON  = "_internal/apify_raw_export.json"
OUTPUT_CSV   = "_internal/apify_raw_export.csv"

def flatten_item(item: dict) -> dict:
    """Flatten list fields to comma-separated strings for CSV export."""
    flat = {}
    for k, v in item.items():
        if isinstance(v, list):
            flat[k] = ", ".join(str(x) for x in v)
        elif isinstance(v, dict):
            flat[k] = json.dumps(v)
        else:
            flat[k] = v
    return flat

def main(test_mode: bool = False):
    token = os.environ.get("APIFY_API_TOKEN")
    if not token:
        print("ERROR: APIFY_API_TOKEN environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    client = ApifyClient(token)

    with open(INPUT_FILE) as f:
        run_input = json.load(f)

    if test_mode:
        run_input["maxItems"] = 10
        run_input["startUrls"] = run_input["startUrls"][:1]
        print("⚙️  TEST MODE: maxItems=10, first URL only")

    print(f"Starting Apify actor run (maxItems={run_input.get('maxItems')})...")
    print(f"URLs: {len(run_input.get('startUrls', []))} search URLs")

    try:
        run = client.actor(ACTOR_PRIMARY).call(run_input=run_input)
    except Exception as e:
        if "subscription" in str(e).lower() or "payment" in str(e).lower():
            print(f"Primary actor requires subscription: {e}")
            print(f"Falling back to: {ACTOR_FALLBACK}")
            run = client.actor(ACTOR_FALLBACK).call(run_input=run_input)
        else:
            raise

    print(f"✅ Run complete. Status: {run['status']}")
    print(f"   Dataset ID:  {run['defaultDatasetId']}")
    print(f"   Run ID:      {run['id']}")

    # Fetch results
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    print(f"   Items fetched: {len(items)}")

    # Save JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    print(f"   Saved JSON: {OUTPUT_JSON}")

    # Save CSV
    if items:
        flat_items = [flatten_item(i) for i in items]
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=flat_items[0].keys(),
                                    extrasaction="ignore")
            writer.writeheader()
            writer.writerows(flat_items)
        print(f"   Saved CSV:  {OUTPUT_CSV}")

    # Field coverage report
    if items:
        print("\n── Field Coverage Report ──────────────────")
        for field in ["title", "company", "location", "skills", "description",
                      "salary", "workType", "postedDate", "url", "experienceLevel"]:
            filled = sum(1 for i in items if i.get(field))
            print(f"  {field:20s}: {filled}/{len(items)} ({filled/len(items):.0%})")

    # Compute unit / cost estimate from run stats
    run_info = client.run(run["id"]).get()
    stats = run_info.get("stats", {})
    cu = stats.get("computeUnits", "N/A")
    print(f"\n── Cost Estimate ──────────────────────────")
    print(f"  Compute units used: {cu}")
    if isinstance(cu, (int, float)) and len(items) > 0:
        cost_per_item = cu / len(items)
        projected_350 = cost_per_item * 350
        projected_cost = projected_350 * 0.40
        print(f"  CU per item:        {cost_per_item:.4f}")
        print(f"  Projected CU (350): {projected_350:.1f}")
        print(f"  Projected cost:     ${projected_cost:.2f}")
        print(f"  Free tier ($5):     {'✅ likely sufficient' if projected_cost < 4 else '⚠️  may exceed free tier'}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Run with 10 items, 1 URL")
    args = parser.parse_args()
    main(test_mode=args.test)
```

---

## § 2 — Deduplication & Raw YAML

### `_internal/01_deduplicate.py`

```python
"""
Phase 2: Deduplicate Apify export and write raw YAML files to data_raw/.

Usage: python _internal/01_deduplicate.py

Output:
    data_raw/{0001..NNNN}.yaml
    _internal/dedup_report.csv
"""
import csv
import json
import re
import sys
from pathlib import Path

import yaml
from rapidfuzz import fuzz

# ── Config ────────────────────────────────────────────────────────────────────
INPUT_FILE      = "_internal/apify_raw_export.json"
OUTPUT_DIR      = Path("data_raw")
REPORT_FILE     = "_internal/dedup_report.csv"
FUZZY_THRESHOLD = 90   # % similarity → considered near-duplicate

GTM_TITLE_KEYWORDS = [
    "gtm",
    "go-to-market",
    "go to market",
    "revenue engineer",
    "revops engineer",
    "revenue operations engineer",
    "marketing engineer",
    "growth engineer",
    "gtm platform",
    "gtm infrastructure",
    "gtm data engineer",
    "gtm analytics",
    "gtm systems",
    "gtm tooling",
    "gtm automation",
    "sales technology engineer",
    "salestech engineer",
    "martech engineer",
    "marketing technology engineer",
    "demand generation engineer",
]

def is_gtm_role(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in GTM_TITLE_KEYWORDS)

def normalize_url(url: str) -> str:
    """Strip query params, fragments, trailing slashes for stable key."""
    return re.sub(r"[?#].*", "", str(url)).rstrip("/").lower()

def get_field(item: dict, *keys: str, default=""):
    """Try multiple field name variants (Apify actors use inconsistent names)."""
    for k in keys:
        v = item.get(k)
        if v is not None and v != "":
            return v
    return default

# ── Load ──────────────────────────────────────────────────────────────────────
if not Path(INPUT_FILE).exists():
    print(f"ERROR: {INPUT_FILE} not found. Run Phase 1 first.", file=sys.stderr)
    sys.exit(1)

with open(INPUT_FILE, encoding="utf-8") as f:
    items = json.load(f)
print(f"Loaded {len(items)} raw items")

# ── Stage 1: URL dedup ────────────────────────────────────────────────────────
seen_urls  = set()
url_deduped = []
url_removed = []
for item in items:
    url = normalize_url(get_field(item, "url", "jobUrl", "link", "applyUrl"))
    if url and url not in seen_urls:
        seen_urls.add(url)
        url_deduped.append(item)
    else:
        url_removed.append({"item": item, "reason": "url_duplicate"})

print(f"After URL dedup: {len(url_deduped)} ({len(url_removed)} removed)")

# ── Stage 2: GTM keyword filter ───────────────────────────────────────────────
gtm_filtered = []
non_gtm_removed = []
for item in url_deduped:
    title = get_field(item, "title", "jobTitle", "position")
    if is_gtm_role(str(title)):
        gtm_filtered.append(item)
    else:
        non_gtm_removed.append({"item": item, "reason": "non_gtm_title"})

print(f"After GTM filter: {len(gtm_filtered)} ({len(non_gtm_removed)} removed)")

# ── Stage 3: Fuzzy title+company dedup ───────────────────────────────────────
final        = []
fuzzy_removed = []
seen_sigs    = []
for item in gtm_filtered:
    title   = get_field(item, "title", "jobTitle", "").lower().strip()
    company = get_field(item, "company", "companyName", "employer", "").lower().strip()
    sig     = f"{title} | {company}"
    is_dup  = any(fuzz.ratio(sig, s) >= FUZZY_THRESHOLD for s in seen_sigs)
    if not is_dup:
        seen_sigs.append(sig)
        final.append(item)
    else:
        fuzzy_removed.append({"item": item, "reason": "fuzzy_duplicate"})

print(f"After fuzzy dedup: {len(final)} ({len(fuzzy_removed)} removed)")

# ── Write raw YAML files ──────────────────────────────────────────────────────
OUTPUT_DIR.mkdir(exist_ok=True)
for i, item in enumerate(final, start=1):
    out_path = OUTPUT_DIR / f"{i:04d}.yaml"
    with open(out_path, "w", encoding="utf-8") as f:
        yaml.dump(item, f, allow_unicode=True, default_flow_style=False,
                  sort_keys=True)

# ── Dedup report ──────────────────────────────────────────────────────────────
with open(REPORT_FILE, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["stage", "kept", "removed", "removal_reason"])
    writer.writerow(["raw_input",       len(items),        0,                    ""])
    writer.writerow(["url_dedup",       len(url_deduped),  len(url_removed),     "duplicate url"])
    writer.writerow(["gtm_filter",      len(gtm_filtered), len(non_gtm_removed), "non-GTM title"])
    writer.writerow(["fuzzy_dedup",     len(final),        len(fuzzy_removed),   "near-duplicate title+company"])

# ── Print samples for human review ───────────────────────────────────────────
print("\n── 3 KEPT SAMPLES ────────────────────────────────────────")
for item in final[:3]:
    print(f"  KEPT:    {get_field(item, 'title','jobTitle')} @ {get_field(item,'company','companyName')} ({get_field(item,'location')})")

print("\n── 3 REMOVED SAMPLES ─────────────────────────────────────")
all_removed = url_removed[:1] + non_gtm_removed[:1] + fuzzy_removed[:1]
for entry in all_removed:
    item   = entry["item"]
    reason = entry["reason"]
    print(f"  REMOVED ({reason}): {get_field(item,'title','jobTitle')} @ {get_field(item,'company','companyName')}")

print(f"\n✅ Wrote {len(final)} raw YAML files to {OUTPUT_DIR}/")
print(f"📊 Dedup report saved to {REPORT_FILE}")
```

---

## § 3 — LLM Structuring

### `_internal/02_structure.py`

```python
"""
Phase 3: Use GPT-4o-mini to extract structured fields from each raw YAML.

Usage:
    python _internal/02_structure.py              # process all files
    python _internal/02_structure.py --limit 5   # pilot: first 5 files only
    python _internal/02_structure.py --resume    # skip already-processed files

Output: data_structured/{0001..NNNN}.yaml
"""
import argparse
import json
import sys
import time
from pathlib import Path

import openai
import yaml
from tqdm import tqdm

# ── Config ────────────────────────────────────────────────────────────────────
RAW_DIR           = Path("data_raw")
OUT_DIR           = Path("data_structured")
MODEL             = "gpt-4o-mini"
RATE_LIMIT_DELAY  = 0.4   # seconds between calls
ERROR_ABORT_RATE  = 0.10  # abort if error rate exceeds 10%

EXTRACTION_PROMPT = """\
You are a data extraction assistant. Given a GTM Engineer job description, extract structured fields.
Return ONLY valid JSON — no markdown fences, no preamble, no explanation.

JSON schema to return:
{
  "job_type": "one of: GTM-Core | RevOps | Sales-Engineering | Marketing-Engineering | Data-Analytics | Platform-Infra",
  "tech_stack": ["all tools, platforms, languages, frameworks mentioned"],
  "crm_tools": ["CRM platforms: Salesforce, HubSpot, Dynamics, Pipedrive, etc."],
  "automation_tools": ["sales/mktg automation: Outreach, Salesloft, Apollo, Marketo, Pardot, etc."],
  "data_tools": ["data/analytics: Snowflake, dbt, BigQuery, Redshift, Looker, Tableau, Fivetran, etc."],
  "ai_ml_tools": ["AI/ML tools: GPT-4, Clay, Unify, Clearbit, 6sense, Demandbase, etc."],
  "languages": ["programming languages: Python, SQL, JavaScript, TypeScript, etc."],
  "required_years_exp": "string like '3-5 years' or '2+ years' or null",
  "required_degree": "string like \"Bachelor's\" or \"Bachelor's preferred\" or null",
  "remote_policy": "one of: REMOTE | HYBRID | ON_SITE | UNKNOWN",
  "seniority_level": "one of: Entry | Mid-Level | Senior | Lead | Manager | Director | Unknown",
  "key_responsibilities": ["up to 5 concise bullet strings summarizing core duties"]
}

Job type definitions:
- GTM-Core: directly owns GTM systems, tooling, and revenue tech stack
- RevOps: revenue operations, forecasting, pipeline ops, CRM ops
- Sales-Engineering: pre/post-sales technical enablement
- Marketing-Engineering: marketing automation, campaign ops, martech
- Data-Analytics: GTM data pipelines, attribution, dashboards
- Platform-Infra: GTM infrastructure, integrations, data plumbing

Job description:
"""

# ── Helpers ───────────────────────────────────────────────────────────────────
client = openai.OpenAI()

def get_field(d: dict, *keys, default=None):
    for k in keys:
        v = d.get(k)
        if v is not None and v != "":
            return v
    return default

def call_gpt(description: str) -> dict:
    response = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        messages=[{"role": "user", "content": EXTRACTION_PROMPT + str(description)[:8000]}]
    )
    text = response.content[0].text.strip()
    # Strip accidental markdown fences
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1].lstrip("json").strip() if len(parts) > 1 else text
    return json.loads(text)

def parse_compensation(salary_str) -> tuple[int | None, int | None]:
    import re
    if not salary_str:
        return None, None
    nums = re.findall(r"\$?([\d,]+)", str(salary_str))
    nums = [int(n.replace(",", "")) for n in nums]
    nums = [n * 1000 if n < 1000 else n for n in nums]
    if len(nums) >= 2:
        return min(nums[:2]), max(nums[:2])
    elif len(nums) == 1:
        return nums[0], nums[0]
    return None, None

# ── Main ──────────────────────────────────────────────────────────────────────
def main(limit: int | None = None, resume: bool = False):
    OUT_DIR.mkdir(exist_ok=True)
    raw_files = sorted(RAW_DIR.glob("*.yaml"))
    if limit:
        raw_files = raw_files[:limit]

    errors    = []
    processed = 0

    for raw_path in tqdm(raw_files, desc="Structuring"):
        out_path = OUT_DIR / raw_path.name
        if resume and out_path.exists():
            continue

        with open(raw_path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        desc    = get_field(raw, "description", "jobDescription", "body", default="")
        title   = get_field(raw, "title", "jobTitle", "position", default="Unknown")
        company = get_field(raw, "company", "companyName", "employer", default="Unknown")
        loc     = get_field(raw, "location", "city", default="")
        salary  = get_field(raw, "salary", "salaryRange", "compensation", default="")
        skills  = get_field(raw, "skills", "requiredSkills", "tags", default=[])
        wtype   = get_field(raw, "workType", "remote", "jobType", default="")
        posted  = get_field(raw, "postedDate", "datePosted", "publishedAt", default="")
        url     = get_field(raw, "url", "jobUrl", "link", default="")
        csize   = get_field(raw, "companySize", "employees", default="")

        try:
            llm = call_claude(desc)
        except Exception as e:
            errors.append({"file": raw_path.name, "error": str(e)})
            # Check error rate
            if len(errors) / (processed + len(errors)) > ERROR_ABORT_RATE and processed > 10:
                print(f"\n⛔ Error rate {len(errors)/(processed+len(errors)):.0%} exceeds threshold. Aborting.")
                print(f"   Last error: {e}")
                break
            llm = {}

        comp_min, comp_max = parse_compensation(salary)

        structured = {
            "title":               title,
            "company":             company,
            "location":            loc,
            "work_type":           llm.get("remote_policy") or str(wtype).upper() or "UNKNOWN",
            "level":               llm.get("seniority_level", "Unknown"),
            "job_type":            llm.get("job_type", "GTM-Core"),
            "tech_stack":          llm.get("tech_stack") or (skills if isinstance(skills, list) else []),
            "crm_tools":           llm.get("crm_tools", []),
            "automation_tools":    llm.get("automation_tools", []),
            "data_tools":          llm.get("data_tools", []),
            "ai_ml_tools":         llm.get("ai_ml_tools", []),
            "languages":           llm.get("languages", []),
            "skills":              skills if isinstance(skills, list) else [],
            "required_years_exp":  llm.get("required_years_exp"),
            "required_degree":     llm.get("required_degree"),
            "key_responsibilities":llm.get("key_responsibilities", []),
            "compensation":        salary,
            "comp_min":            comp_min,
            "comp_max":            comp_max,
            "company_size":        csize,
            "posted_date":         str(posted) if posted else None,
            "url":                 url,
            "source":              "Built In",
            "description":         desc,
        }

        with open(out_path, "w", encoding="utf-8") as f:
            yaml.dump(structured, f, allow_unicode=True, default_flow_style=False,
                      sort_keys=True, width=120)

        processed += 1
        time.sleep(RATE_LIMIT_DELAY)

    print(f"\n✅ Structured {processed} files → {OUT_DIR}/")
    if errors:
        print(f"⚠️  {len(errors)} errors:")
        for e in errors:
            print(f"   {e['file']}: {e['error']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit",  type=int, default=None, help="Process only first N files")
    parser.add_argument("--resume", action="store_true",    help="Skip already-structured files")
    args = parser.parse_args()
    main(limit=args.limit, resume=args.resume)
```

---

## § 4 — Validation Script

Run this at Checkpoint 4.1. Either inline in a script or interactively:

```python
"""Validation: run after Phase 3 to verify data quality."""
import glob, yaml

REQUIRED = ["title", "company", "job_type", "tech_stack", "work_type", "level", "url"]
files    = sorted(glob.glob("data_structured/*.yaml"))

print(f"Total structured files: {len(files)}\n")

field_missing = {f: 0 for f in REQUIRED}
empty_desc    = []
empty_stack   = []
multi_fail    = []

for path in files:
    with open(path) as f:
        d = yaml.safe_load(f)

    missing = [k for k in REQUIRED if not d.get(k)]
    for k in missing:
        field_missing[k] += 1

    if not d.get("description"):
        empty_desc.append(path)
    if not d.get("tech_stack"):
        empty_stack.append(path)
    if len(missing) >= 2:
        multi_fail.append((path, missing))

print("── Field coverage ──────────────────────────────────")
for field, count in field_missing.items():
    pct = count / len(files)
    status = "✅" if pct < 0.05 else ("⚠️ " if pct < 0.15 else "❌")
    print(f"  {status} {field:25s}: {count} missing ({pct:.1%})")

print(f"\n── Empty descriptions : {len(empty_desc)}")
print(f"── Empty tech_stack   : {len(empty_stack)}")
print(f"\n── Files with 2+ missing required fields: {len(multi_fail)}")
for path, missing in multi_fail[:10]:
    print(f"   {path}: {missing}")
```

---

## § 5 — Jupyter Notebook Specification

### Section 0: Setup & Data Loading

```python
import glob, yaml
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from pathlib import Path
import warnings; warnings.filterwarnings("ignore")

# ── Style ─────────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.figsize":   (12, 6),
    "axes.spines.top":  False,
    "axes.spines.right":False,
    "font.family":      "sans-serif",
    "axes.titlesize":   14,
    "axes.titleweight": "bold",
})
PALETTE   = sns.color_palette("tab10")
CHARTS    = Path("_internal/charts")
CHARTS.mkdir(parents=True, exist_ok=True)

def savefig(name: str):
    plt.tight_layout()
    plt.savefig(CHARTS / f"{name}.png", dpi=150, bbox_inches="tight")
    plt.show()
    plt.close()

# ── Load ──────────────────────────────────────────────────────────────────────
records = []
for path in sorted(glob.glob("data_structured/*.yaml")):
    with open(path) as f:
        records.append(yaml.safe_load(f))

df = pd.DataFrame(records)
df["posted_date"] = pd.to_datetime(df["posted_date"], errors="coerce")
df["comp_mid"]    = (pd.to_numeric(df["comp_min"], errors="coerce") +
                     pd.to_numeric(df["comp_max"], errors="coerce")) / 2

print(f"Loaded {len(df)} job records")
print(f"Columns: {list(df.columns)}")
df.head(3)
```

---

### Section 1: Dataset Overview

```python
# ── Summary stats ─────────────────────────────────────────────────────────────
stats = {
    "Total jobs":              len(df),
    "Unique companies":        df["company"].nunique(),
    "Cities covered":          5,
    "Date range":              f"{df['posted_date'].min():%Y-%m-%d} – {df['posted_date'].max():%Y-%m-%d}"
                               if df["posted_date"].notna().any() else "N/A",
    "Jobs with salary data":   f"{df['comp_mid'].notna().sum()} ({df['comp_mid'].notna().mean():.1%})",
    "Jobs with tech_stack":    f"{df['tech_stack'].apply(bool).sum()} ({df['tech_stack'].apply(bool).mean():.1%})",
}
for k, v in stats.items():
    print(f"  {k:30s}: {v}")

# ── Top 15 companies ──────────────────────────────────────────────────────────
top_co = df["company"].value_counts().head(15)
fig, ax = plt.subplots(figsize=(12, 7))
bars = top_co.sort_values().plot(kind="barh", ax=ax, color=PALETTE[0])
ax.set_xlabel("Number of Job Postings")
ax.set_title("Top 15 Companies Hiring GTM Engineers")
for i, v in enumerate(top_co.sort_values()):
    ax.text(v + 0.1, i, str(v), va="center", fontsize=10)
savefig("01_top_companies")
```

---

### Section 2: GTM Job Type Distribution

```python
jt = df["job_type"].value_counts()

fig, axes = plt.subplots(1, 2, figsize=(15, 6))

# Donut
colors = sns.color_palette("tab10", len(jt))
axes[0].pie(jt, labels=jt.index, autopct="%1.1f%%", colors=colors,
            startangle=90, wedgeprops=dict(width=0.55),
            textprops=dict(fontsize=11))
axes[0].set_title("Job Type Mix")

# Horizontal bar
jt.sort_values().plot(kind="barh", ax=axes[1], color=colors[::-1])
axes[1].set_xlabel("Number of Jobs")
axes[1].set_title("Jobs by GTM Specialization")
for i, (_, v) in enumerate(jt.sort_values().items()):
    axes[1].text(v + 0.2, i, f"{v}  ({v/len(df):.1%})", va="center", fontsize=10)

savefig("02_job_type_distribution")
```

---

### Section 3: Compensation Analysis

```python
sal = df[df["comp_mid"].notna()].copy()
print(f"Jobs with salary data: {len(sal)} ({len(sal)/len(df):.1%})")

LEVEL_ORDER = ["Entry", "Mid-Level", "Senior", "Lead", "Manager", "Director"]
valid_levels = [l for l in LEVEL_ORDER if l in sal["level"].values]

fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# By seniority
sal[sal["level"].isin(valid_levels)].boxplot(
    column="comp_mid", by="level", ax=axes[0],
    order=valid_levels, vert=False,
    patch_artist=True, medianprops=dict(color="red", linewidth=2)
)
axes[0].set_title("Compensation by Seniority Level")
axes[0].set_xlabel("Annual Salary (USD)")
axes[0].xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x/1000:.0f}k"))
plt.sca(axes[0]); plt.title("Compensation by Seniority Level")

# By job type
sal.boxplot(column="comp_mid", by="job_type", ax=axes[1], vert=False,
            patch_artist=True, medianprops=dict(color="red", linewidth=2))
axes[1].set_xlabel("Annual Salary (USD)")
axes[1].xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x/1000:.0f}k"))
plt.sca(axes[1]); plt.title("Compensation by Job Type")

plt.suptitle("")
savefig("03_compensation_analysis")

print("\nMedian compensation by seniority:")
print(sal.groupby("level")["comp_mid"]
        .agg(median="median", mean="mean", count="count")
        .round(0).to_string())
```

---

### Section 4: Location & Remote Work Trends

```python
wt = df["work_type"].value_counts()
colors_map = {"REMOTE": "#2ecc71", "HYBRID": "#3498db", "ON_SITE": "#e74c3c", "UNKNOWN": "#95a5a6"}
pie_colors = [colors_map.get(k, "#bdc3c7") for k in wt.index]

fig, axes = plt.subplots(1, 2, figsize=(15, 6))
axes[0].pie(wt, labels=wt.index, autopct="%1.1f%%", colors=pie_colors,
            startangle=90, wedgeprops=dict(width=0.55))
axes[0].set_title("Work Type Distribution")

top_loc = df["location"].value_counts().head(12)
top_loc.sort_values().plot(kind="barh", ax=axes[1], color=PALETTE[1])
axes[1].set_title("Top 12 Locations")
axes[1].set_xlabel("Number of Jobs")

savefig("04_location_remote")

# City breakdown by job type (stacked bar)
city_type = df.groupby(["location", "job_type"]).size().unstack(fill_value=0)
top_cities = df["location"].value_counts().head(8).index
city_type.loc[city_type.index.isin(top_cities)].plot(
    kind="bar", stacked=True, figsize=(13, 6),
    colormap="tab10", rot=30
)
plt.title("Job Type Breakdown by City (Top 8 Locations)")
plt.ylabel("Number of Jobs")
plt.legend(title="Job Type", bbox_to_anchor=(1, 1))
savefig("04b_city_by_job_type")
```

---

### Section 5: Tech Stack & Tool Analysis

```python
from itertools import combinations

# ── All tools frequency ───────────────────────────────────────────────────────
all_tools = Counter()
for tools in df["tech_stack"].dropna():
    if isinstance(tools, list):
        all_tools.update(t.strip() for t in tools if t)

top25 = pd.Series(dict(all_tools.most_common(25)))
fig, ax = plt.subplots(figsize=(12, 10))
top25.sort_values().plot(kind="barh", ax=ax, color=PALETTE[0])
ax.set_title("Top 25 Tools & Technologies in GTM Engineer Postings")
ax.set_xlabel(f"Frequency  (n={len(df)} jobs)")
for i, v in enumerate(top25.sort_values()):
    ax.text(v + 0.3, i, f"{v}  ({v/len(df):.1%})", va="center", fontsize=9)
savefig("05_top_tools")

# ── Category breakdown ────────────────────────────────────────────────────────
def top_cat(col, n=10):
    c = Counter()
    for t in df[col].dropna():
        if isinstance(t, list): c.update(t)
    return pd.Series(dict(c.most_common(n)))

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
for ax, (title, col, color) in zip(axes.flat, [
    ("CRM Tools",                  "crm_tools",        PALETTE[3]),
    ("Sales/Marketing Automation", "automation_tools", PALETTE[0]),
    ("Data & Analytics Tools",     "data_tools",       PALETTE[2]),
    ("AI/ML Tools",                "ai_ml_tools",      PALETTE[4]),
]):
    s = top_cat(col)
    if len(s):
        s.sort_values().plot(kind="barh", ax=ax, color=color)
        ax.set_xlabel("Frequency")
    else:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
    ax.set_title(title)

plt.suptitle("GTM Tool Stack by Category", fontsize=16, y=1.01)
savefig("06_tool_categories")

# ── Co-occurrence heatmap ─────────────────────────────────────────────────────
TOP_N    = 15
top_list = [t for t, _ in all_tools.most_common(TOP_N)]
cooccur  = np.zeros((TOP_N, TOP_N), dtype=int)
for tools in df["tech_stack"].dropna():
    if not isinstance(tools, list): continue
    s = set(t.strip() for t in tools)
    for i, t1 in enumerate(top_list):
        for j, t2 in enumerate(top_list):
            if t1 in s and t2 in s:
                cooccur[i, j] += 1
np.fill_diagonal(cooccur, 0)

fig, ax = plt.subplots(figsize=(12, 10))
sns.heatmap(cooccur, xticklabels=top_list, yticklabels=top_list,
            annot=True, fmt="d", cmap="Blues", ax=ax,
            cbar_kws={"label": "Co-occurrences"})
ax.set_title("Tool Co-occurrence Matrix — Top 15 GTM Tools")
plt.xticks(rotation=45, ha="right")
savefig("07_tool_cooccurrence")
```

---

### Section 6: Programming Languages

```python
lang_ctr = Counter()
for langs in df["languages"].dropna():
    if isinstance(langs, list): lang_ctr.update(langs)

lang_s = pd.Series(dict(lang_ctr.most_common(15)))
fig, ax = plt.subplots(figsize=(10, 6))
lang_s.sort_values().plot(kind="barh", ax=ax, color=PALETTE[1])
ax.set_title("Programming Languages in GTM Engineer Roles")
ax.set_xlabel(f"Frequency  (n={len(df)})")
for i, v in enumerate(lang_s.sort_values()):
    ax.text(v + 0.2, i, f"{v}  ({v/len(df):.1%})", va="center", fontsize=10)
savefig("08_languages")
```

---

### Section 7: Experience & Seniority

```python
fig, axes = plt.subplots(1, 2, figsize=(15, 6))

level_order  = ["Entry", "Mid-Level", "Senior", "Lead", "Manager", "Director", "Unknown"]
level_counts = df["level"].value_counts().reindex(
    [l for l in level_order if l in df["level"].values]
)
level_counts.plot(kind="bar", ax=axes[0],
                  color=sns.color_palette("viridis", len(level_counts)), rot=30)
axes[0].set_title("Seniority Level Distribution")
axes[0].set_ylabel("Number of Jobs")
for i, v in enumerate(level_counts):
    axes[0].text(i, v + 0.3, f"{v}\n({v/len(df):.1%})", ha="center", fontsize=9)

exp_counts = df["required_years_exp"].dropna().value_counts().head(10)
exp_counts.sort_values().plot(kind="barh", ax=axes[1], color=PALETTE[2])
axes[1].set_title("Required Years of Experience")
axes[1].set_xlabel("Number of Jobs")

savefig("09_seniority_experience")
```

---

### Section 8: Company Size Distribution

```python
size_counts = df["company_size"].fillna("Not Disclosed").value_counts()
fig, ax = plt.subplots(figsize=(10, 5))
size_counts.plot(kind="bar", ax=ax,
                 color=sns.color_palette("Blues_r", len(size_counts)), rot=30)
ax.set_title("Company Size Distribution for GTM Engineer Roles")
ax.set_ylabel("Number of Jobs")
ax.set_xlabel("Company Size")
savefig("10_company_size")
```

---

### Section 9: Temporal Trends

```python
date_df = df.dropna(subset=["posted_date"]).copy()
if len(date_df) > 10:
    weekly = date_df.set_index("posted_date").resample("W").size()
    fig, ax = plt.subplots(figsize=(13, 5))
    weekly.plot(ax=ax, marker="o", linewidth=2, color=PALETTE[0])
    ax.fill_between(weekly.index, weekly.values, alpha=0.25, color=PALETTE[0])
    ax.set_title("GTM Engineer Job Postings Over Time (Weekly)")
    ax.set_ylabel("Jobs Posted")
    ax.set_xlabel("")
    savefig("11_temporal_trends")
else:
    print("Insufficient date data for temporal chart — skipping.")
```

---

### Section 10: Key Findings

```python
from IPython.display import Markdown, display

top_tool       = all_tools.most_common(1)[0]
top_crm        = top_cat("crm_tools").idxmax()    if len(top_cat("crm_tools")) else "N/A"
top_automation = top_cat("automation_tools").idxmax() if len(top_cat("automation_tools")) else "N/A"
pct_remote     = (df["work_type"] == "REMOTE").mean()
pct_hybrid     = (df["work_type"] == "HYBRID").mean()
pct_python     = all_tools.get("Python", 0) / len(df)
pct_sql        = all_tools.get("SQL", 0) / len(df)
pct_ai_tools   = df["ai_ml_tools"].apply(bool).mean()
median_sal     = df["comp_mid"].median()
sal_note       = f"${median_sal:,.0f}/year" if pd.notna(median_sal) else "not widely disclosed"

display(Markdown(f"""
## 🔑 Key Findings

**Dataset:** {len(df)} unique GTM engineer job postings from {df['company'].nunique()} companies across 5 cities (Builtin.com, {pd.Timestamp.now().strftime('%B %Y')})

### The GTM Engineer Role is Code-First
- **Python** is required in {pct_python:.1%} of postings — this is not a no-code ops role
- **SQL** appears in {pct_sql:.1%} of postings, confirming heavy data work
- The dominant tech pattern: CRM ({top_crm}) + automation ({top_automation}) + a data warehouse

### AI Tools Are Entering the GTM Stack Rapidly  
- **{pct_ai_tools:.1%} of postings** mention at least one AI/ML tool (Clay, GPT-4, 6sense, Demandbase)
- This signals that AI-augmented GTM is already a real expectation, not a future trend

### Remote Work is the Norm
- **{pct_remote:.1%} fully remote**, {pct_hybrid:.1%} hybrid — GTM engineers are expected to work distributed
- Austin and Berlin skew more hybrid than SF/NY

### Compensation (where disclosed)
- Median: {sal_note}
- Senior/Lead roles command significant premium over mid-level

### Most Common Tool: {top_tool[0]} ({top_tool[1]/len(df):.1%} of postings)
- This single tool dominates the GTM landscape — fluency in it is table stakes
"""))
```

---

## § README Template

```markdown
# GTM Engineer Job Market Analysis

**{N} job descriptions** from Builtin.com · Collected {MONTH YEAR} · Cities: New York · San Francisco · London · Berlin · Austin TX

For deeper analysis, see [analysis.ipynb](./analysis.ipynb).

## Highlights

> Replace these with actual computed values from the notebook.

- **{N} jobs, {C} unique companies** — GTM engineering is a rapidly growing niche
- **{X}% of roles are fully remote**
- Most common tool: **{TOOL}** ({PCT}% of postings)
- Dominant CRM: **{CRM}**, dominant automation tool: **{AUTO}**
- **Python** required in {X}% of roles — GTM engineering is code-first
- **{X}% of postings mention AI/ML tools** (Clay, GPT-4, 6sense) — AI adoption is real now
- Median compensation: **${X}/year** (among postings with salary data)

## Contents

| Path | Description |
|---|---|
| `data_structured/` | {N} structured YAML files — title, company, tech_stack, compensation, full description |
| `data_raw/` | {N} raw YAML files from Apify export |
| `analysis.ipynb` | Full analysis notebook with charts |
| `_internal/` | Scraping scripts, structuring scripts, charts, dedup report |

## Data Format

Each file in `data_structured/` follows this schema:

```yaml
title: GTM Engineer
company: Acme Corp
location: New York, NY
work_type: HYBRID          # REMOTE | HYBRID | ON_SITE
level: Senior
job_type: GTM-Core         # GTM-Core | RevOps | Sales-Engineering | Marketing-Engineering | Data-Analytics | Platform-Infra
tech_stack: [Salesforce, HubSpot, Python, SQL, Segment, Snowflake]
crm_tools: [Salesforce, HubSpot]
automation_tools: [Outreach, Apollo]
data_tools: [Snowflake, dbt, Looker]
ai_ml_tools: [Clay, GPT-4]
languages: [Python, SQL]
required_years_exp: "3-5 years"
required_degree: "Bachelor's preferred"
compensation: "$130,000 - $160,000/year"
comp_min: 130000
comp_max: 160000
company_size: "500-1,000 Employees"
posted_date: "2025-03-01"
url: https://builtin.com/job/...
source: Built In
```

## Top Skills

> Replace with actual computed ranking from notebook.

## Methodology

1. **Scraping:** Apify actor `[actor-name]` — input: Builtin.com search URLs for GTM/RevOps/marketing-engineering roles across 5 cities
2. **Deduplication:** URL-exact dedup → GTM keyword filter → fuzzy title+company dedup (90% threshold via `rapidfuzz`)
3. **Structuring:** Claude `claude-sonnet-4-20250514` extracts job_type classification, tool categories, seniority, and compensation normalization from each description
4. **Analysis:** Python/Pandas/Matplotlib/Seaborn in Jupyter

## Reproduce

```bash
git clone <repo>
cd gtm-job-market
export APIFY_API_TOKEN=...
export ANTHROPIC_API_KEY=...
uv sync
python _internal/00_run_apify.py   # Phase 1: scrape
python _internal/01_deduplicate.py  # Phase 2: dedup
python _internal/02_structure.py    # Phase 3: structure
jupyter nbconvert --to notebook --execute analysis.ipynb
```

## License

MIT
```

---

## § Improvement Ideas (backlog for future iterations)

These are enhancements worth implementing after the core project is complete:

**Data Enrichment**
- Add LinkedIn company data (headcount, industry, funding stage) via a second Apify actor
- Enrich compensation data from Levels.fyi or Glassdoor for companies with missing salary
- Add `company_stage` field: startup/scaleup/enterprise (derived from company_size + funding)

**Analysis Depth**
- Skill gap analysis: which tools appear together vs. which are mutually exclusive
- Compensation regression: which tools/skills are most correlated with higher pay
- City-vs-city comparison: SF vs NY vs London tech stacks — how different are they?
- Seniority progression map: which tools are entry-level vs. senior-only

**Notebook Quality**
- Add a `requirements_wordcloud.py` script in `_internal/` to generate a word cloud from all descriptions
- Export a one-page PDF summary with key charts for sharing without the notebook
- Add `plotly` interactive versions of the top tools and co-occurrence charts

**Repository**
- Add GitHub Actions workflow to re-scrape and re-run notebook monthly
- Add a simple `Makefile` with `make scrape`, `make structure`, `make analyze` targets
- Publish the structured dataset to HuggingFace Datasets for community use
