import json
import yaml
import os
import re

INPUT_FILE = "_internal/structured_jobs.json"
OUTPUT_DIR = "data_structured"

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]', '-', text)
    return re.sub(r'-+', '-', text).strip('-')

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    count = 0
    for job in data:
        if job.get("is_gtm_technical"):
            # Create a filename based on company and title
            company = slugify(job.get("company", "unknown"))
            title = slugify(job.get("title", "job"))
            filename = f"{company}-{title}.yaml"
            
            # Ensure unique filename if multiple jobs from same company have same title
            full_path = os.path.join(OUTPUT_DIR, filename)
            counter = 1
            while os.path.exists(full_path):
                full_path = os.path.join(OUTPUT_DIR, f"{company}-{title}-{counter}.yaml")
                counter += 1
            
            with open(full_path, 'w', encoding='utf-8') as f:
                yaml.dump(job, f, sort_keys=False, allow_unicode=True)
            count += 1

    print(f"✅ Exported {count} YAML files to {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
