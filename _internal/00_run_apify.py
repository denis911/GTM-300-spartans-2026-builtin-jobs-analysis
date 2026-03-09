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
import pandas as pd

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

    # Use absolute path for input file to avoid CWD issues
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(base_dir, INPUT_FILE)
    output_json_path = os.path.join(base_dir, OUTPUT_JSON)
    output_csv_path = os.path.join(base_dir, OUTPUT_CSV)

    with open(input_path) as f:
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
        error_msg = str(e).lower()
        if "subscription" in error_msg or "payment" in error_msg or "paid" in error_msg or "403" in error_msg:
            print(f"⚠️ Primary actor requires subscription or returned 403: {e}")
            print(f"🔄 Falling back to: {ACTOR_FALLBACK}")
            run = client.actor(ACTOR_FALLBACK).call(run_input=run_input)
        else:
            print(f"❌ Unexpected error calling primary actor: {e}")
            raise

    print(f"✅ Run complete. Status: {run['status']}")
    print(f"   Dataset ID:  {run['defaultDatasetId']}")
    print(f"   Run ID:      {run['id']}")

    # Fetch results
    raw_items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    print(f"   Items fetched: {len(raw_items)}")

    # Normalize results for fallback scraper
    items = []
    for item in raw_items:
        normalized = item.copy()
        # Map fields if they are missing but present in other formats
        if not normalized.get("description") and normalized.get("description_text"):
            normalized["description"] = normalized["description_text"]
        if not normalized.get("postedDate") and normalized.get("date_posted"):
            normalized["postedDate"] = normalized["date_posted"]
        
        # Construct salary string if missing
        if not normalized.get("salary") and normalized.get("salary_json_min"):
            min_val = normalized.get("salary_json_min")
            max_val = normalized.get("salary_json_max")
            currency = normalized.get("salary_json_currency", "USD")
            if min_val and max_val:
                normalized["salary"] = f"{currency} {min_val:,} - {max_val:,}"
            elif min_val:
                normalized["salary"] = f"{currency} {min_val:,}+"

        # Map workType
        if not normalized.get("workType") and normalized.get("workplace_type"):
            normalized["workType"] = normalized["workplace_type"]

        items.append(normalized)

    # Save JSON
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    print(f"   Saved JSON: {output_json_path}")

    # Save CSV
    if items:
        # We need a more robust way to flatten/handle different field sets for CSV
        df = pd.DataFrame(items)
        df.to_csv(output_csv_path, index=False, encoding="utf-8-sig")
        print(f"   Saved CSV:  {output_csv_path}")

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
