from scraper.google_scraper import Google
from scraper.utils import create_scraper_input
import pandas as pd
import os
if __name__ == "__main__":
    scraper = Google()
    scraper_input = create_scraper_input(
        search_term="Traffic Engineer",
        location="US",
        results_wanted=20,
        hours_old=72,
        is_remote=True
    )
    jobs = scraper.scrape(scraper_input).to_df()
    print(f"Found {len(jobs)} jobs")
    print(jobs.head())
    os.makedirs("data", exist_ok=True)
    jobs.to_csv("data/google_jobs.csv", index=False)
