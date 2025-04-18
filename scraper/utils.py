import re
import requests
from scraper.models import ScraperInput

def create_session():
    session = requests.Session()
    return session

def extract_emails_from_text(text):
    return re.findall(r"[\w\.-]+@[\w\.-]+", text or "")

def extract_job_type(text):
    if "full-time" in text.lower():
        return "Full Time"
    elif "part-time" in text.lower():
        return "Part Time"
    elif "intern" in text.lower():
        return "Internship"
    elif "contract" in text.lower():
        return "Contract"
    return None

def find_job_info(jobs_data):
    if isinstance(jobs_data, dict):
        for key, value in jobs_data.items():
            if key == "520084652" and isinstance(value, list):
                return value
            else:
                result = find_job_info(value)
                if result:
                    return result
    elif isinstance(jobs_data, list):
        for item in jobs_data:
            result = find_job_info(item)
            if result:
                return result
    return None

def find_job_info_initial_page(html_text):
    pattern = f'520084652":(' + r"\[.*?\]\s*])\s*}\s*]\s*]\s*]\s*]"
    results = []
    matches = re.finditer(pattern, html_text)

    import json
    for match in matches:
        try:
            parsed_data = json.loads(match.group(1))
            results.append(parsed_data)
        except json.JSONDecodeError:
            continue
    return results

def create_scraper_input(search_term, location, results_wanted, hours_old, is_remote):
    return ScraperInput(
        search_term=search_term,
        location=location,
        results_wanted=results_wanted,
        hours_old=hours_old,
        is_remote=is_remote
    )
def extract_salary(description):
    if not description:
        return "N/A"

    match = re.search(r"\$?\s?(\d{2,3}[,\d{3}]*)\s?[-to–~]?\s?\$?(\d{2,3}[,\d{3}]*)", description, re.IGNORECASE)
    if match:
        return f"${match.group(1)} - ${match.group(2)}"
    return "N/A"
