# GTM Engineer Job Market Analysis

**~300 job descriptions** from Builtin.com · Collected March 2026 · Cities: New York · San Francisco · London · Berlin · Austin TX

Collect ~300 GTM (Go-To-Market) Engineer job descriptions from Builtin.com, structured by city, clean and normalize the data with an LLM extraction step, run a comprehensive Jupyter notebook analysis, and produce GitHub-ready documentation.

Original idea is taken from repository AI Engineering research: https://github.com/alexeygrigorev/ai-engineering-field-guide/tree/main/job-market

## Contents

| Path | Description |
|---|---|
| `data_structured/` | Structured YAML files — title, company, tech_stack, compensation |
| `data_raw/` | Raw YAML files from Apify export |
| `analysis.ipynb` | Full analysis notebook with charts |
| `_internal/` | Scraping scripts, structuring scripts, charts, dedup report |

## Prerequisites

Before running the pipeline, you need to set up your API keys.

### 1. Get Your Keys
- **Apify API Token**: Sign up at [Apify](https://apify.com/) and find your token in Settings > Integrations.
- **OpenAI API Key**: Get your key from the [OpenAI Dashboard](https://platform.openai.com/).

### 2. Setup Environment Variables (Windows 11)

To make these keys available to the scripts, follow these steps:

#### Option A: Persistent (via System UI)
1. Press `Win + R`, type `sysdm.cpl`, and press Enter.
2. Go to the **Advanced** tab and click **Environment Variables**.
3. Under **User variables**, click **New**:
   - Variable name: `APIFY_API_TOKEN`
   - Variable value: `your_token_here`
4. Click **New** again:
   - Variable name: `OPENAI_API_KEY`
   - Variable value: `your_key_here`
5. Click OK on all windows and **restart your terminal**.

#### Option B: Temporary (PowerShell)
```powershell
$env:APIFY_API_TOKEN = "your_token_here"
$env:OPENAI_API_KEY = "your_key_here"
```
#### How to check if environment variables are set
```powershell
echo $APIFY_API_TOKEN
echo $OPENAI_API_KEY
```

or in Win 11 CMD:
```cmd
echo %APIFY_API_TOKEN%
echo %OPENAI_API_KEY%
```


### 3. Apify Actors (Automatic Fallback)
The scraping script `_internal/00_run_apify.py` handles actor selection automatically:
- **Primary**: `easyapi/builtin-jobs-scraper` (Optimized, may require subscription)
- **Fallback**: `shahidirfan/builtin-jobs-scraper` (Free-tier friendly)

If the primary actor returns a 403 (Subscription/Proxy error), the script automatically switches to the fallback. Data is normalized across both actors to maintain consistent fields (`title`, `company`, `description`, etc.).

---

*Code and analysis by Antigravity AI, inspired by the AI Engineering Field Guide.*
