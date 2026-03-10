import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- CONFIGURATION ---
INPUT_FILE = "_internal/structured_jobs.json"
OUTPUT_DIR = "_internal/charts"
STATS_FILE = "_internal/summary_stats.json"

# Set premium aesthetic
plt.style.use('dark_background')
sns.set_theme(style="darkgrid", palette="muted")
COLOR_PALETTE = sns.color_palette("viridis", as_cmap=False)

def load_data():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return None
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    # Filter for GTM Technical roles
    if "is_gtm_technical" in df.columns:
        df = df[df["is_gtm_technical"] == True].copy()
    return df

def analyze_tech_stack(df):
    if "tech_stack" not in df.columns:
        return
    
    # Flatten the list of tools
    all_tools = []
    for tools in df["tech_stack"].dropna():
        if isinstance(tools, list):
            all_tools.extend(tools)
    
    tool_counts = pd.Series(all_tools).value_counts().head(15)
    
    plt.figure(figsize=(12, 7))
    sns.barplot(x=tool_counts.values, y=tool_counts.index, hue=tool_counts.index, palette="viridis", legend=False)
    plt.title("Top 15 GTM Engineering Tools (March 2026)", fontsize=16, fontweight='bold', pad=20)
    plt.xlabel("Number of Job Postings", fontsize=12)
    plt.ylabel("Tool / Technology", fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "tech_stack_popularity.png"), dpi=300)
    plt.close()
    
    return tool_counts.to_dict()

def analyze_salaries(df):
    # Ensure numeric
    df["salary_min"] = pd.to_numeric(df["salary_min"], errors='coerce')
    df["salary_max"] = pd.to_numeric(df["salary_max"], errors='coerce')
    
    # Drop rows without salary data for this chart
    sal_df = df.dropna(subset=["salary_min", "salary_max", "seniority"])
    sal_df = sal_df[sal_df["salary_min"] > 0] # Filter out noise
    
    if sal_df.empty:
        print("No valid salary data found for plotting.")
        return {}

    # Average salary for the boxplot
    sal_df["avg_salary"] = (sal_df["salary_min"] + sal_df["salary_max"]) / 2
    
    # Order seniority for better visualization
    order = ["Junior", "Mid", "Senior", "Lead", "Staff", "Manager", "Head"]
    current_order = [o for o in order if o in sal_df["seniority"].unique()]
    
    plt.figure(figsize=(12, 7))
    sns.boxplot(data=sal_df, x="seniority", y="avg_salary", order=current_order, palette="magma", hue="seniority", legend=False)
    plt.title("GTM Engineer Salary Ranges by Seniority (USD)", fontsize=16, fontweight='bold', pad=20)
    plt.ylabel("Annual Base Salary (USD)", fontsize=12)
    plt.xlabel("Seniority Level", fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "salary_by_seniority.png"), dpi=300)
    plt.close()
    
    stats = sal_df.groupby("seniority")["avg_salary"].agg(["mean", "median", "count"]).to_dict("index")
    return stats

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    df = load_data()
    if df is None: return

    print(f"📊 Analyzing {len(df)} GTM Technical roles...")
    
    tech_stats = analyze_tech_stack(df)
    salary_stats = analyze_salaries(df)
    
    summary = {
        "total_gtm_roles": len(df),
        "top_tools": tech_stats,
        "salary_stats": salary_stats
    }
    
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=4)
        
    print(f"✨ Analysis complete. Charts saved to {OUTPUT_DIR}")
    print(f"📈 Summary stats saved to {STATS_FILE}")

if __name__ == "__main__":
    main()
