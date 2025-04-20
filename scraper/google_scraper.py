import re
import json
from datetime import datetime, timedelta

from scraper.constants import (
    get_headers_initial,
    get_headers_jobs,
    extract_async_param,
)
from scraper.utils import (
    extract_emails_from_text,
    extract_job_type,
    extract_salary,
    create_session,
    find_job_info_initial_page,
    find_job_info,
)
from scraper.models import ScraperInput, JobPost, JobResponse, Location


class Google:
    def __init__(self):
        # Initialize HTTP session
        self.session = create_session()
        self.jobs_per_page = 10
        self.url = "https://www.google.com/search"
        self.jobs_url = "https://www.google.com/async/callback:550"

        # These will be set during the first request
        self.current_user_agent = None
        self.async_param = ""

        self.scraper_input = None
        self.seen_urls = set()

    def scrape(self, scraper_input: ScraperInput) -> JobResponse:
        self.scraper_input = scraper_input

        # Get initial forward cursor and first batch of jobs
        forward_cursor, job_list = self._get_initial_cursor_and_jobs()
        print(f"Initial jobs: {len(job_list)}, Forward cursor: {forward_cursor}")

        if not forward_cursor:
            return JobResponse(jobs=job_list)

        # Keep fetching until we've reached the desired number
        while len(self.seen_urls) < scraper_input.results_wanted and forward_cursor:
            try:
                jobs, forward_cursor = self._get_jobs_next_page(forward_cursor)
                print(f"Fetched {len(jobs)} more jobs. New cursor: {forward_cursor}")
                if not jobs:
                    break
                job_list += jobs
            except Exception as e:
                print(f"Error fetching next page: {e}")
                break

        # Trim to the number wanted
        return JobResponse(jobs=job_list[:scraper_input.results_wanted])

    def _get_initial_cursor_and_jobs(self):
        # Build search query
        query = self.scraper_input.google_search_term or f"{self.scraper_input.search_term} jobs"
        if self.scraper_input.location:
            query += f" near {self.scraper_input.location}"
        if self.scraper_input.is_remote:
            query += " remote"

        params = {"q": query, "udm": "8"}

        # Rotate UA and fetch initial page
        initial_headers = get_headers_initial()
        self.current_user_agent = initial_headers["User-Agent"]
        response = self.session.get(self.url, headers=initial_headers, params=params)

        # Extract async parameter for AJAX calls (fallback to empty string)
        try:
            token = extract_async_param(response.text)
            self.async_param = token if token else ""
        except Exception:
            print("[WARN] asyncParam not found; continuing without it.")
            self.async_param = ""

        # Extract forward cursor from HTML
        match_fc = re.search(r'data-async-fc="([^"]+)"', response.text)
        forward_cursor = match_fc.group(1) if match_fc else None

        # Parse initial jobs
        jobs_raw = find_job_info_initial_page(response.text)
        jobs = [self._parse_job(j) for j in jobs_raw if j]

        return forward_cursor, list(filter(None, jobs))

    def _get_jobs_next_page(self, forward_cursor):
        print(f"[NEXT PAGE] Forward cursor passed in: {forward_cursor}")

        # Prepare params and headers for AJAX request
        ajax_headers = get_headers_jobs(self.current_user_agent)
        params = {"fc": forward_cursor, "fcv": "3"}
        if self.async_param:
            params["async"] = self.async_param

        response = self.session.get(self.jobs_url, headers=ajax_headers, params=params)
        return self._parse_jobs(response.text)

    def _parse_jobs(self, job_data):
        try:
            start_idx = job_data.find("[[[")
            end_idx = job_data.rindex("]]]") + 3
            parsed = json.loads(job_data[start_idx:end_idx])[0]
        except (ValueError, json.JSONDecodeError) as e:
            print(f"[PARSE ERROR] Could not parse job block: {e}")
            with open("raw_next_page.html", "w", encoding="utf-8") as f:
                f.write(job_data)
            return [], None

        # Extract new forward cursor
        match_fc = re.search(r'"fc":"(.*?)"', job_data)
        forward_cursor = match_fc.group(1) if match_fc else None
        print(f"[PARSE PAGE] Extracted new forward_cursor: {forward_cursor}")

        # Parse individual jobs
        jobs = []
        for array in parsed:
            _, inner = array
            if isinstance(inner, str) and inner.startswith("[[["):
                job_d = json.loads(inner)
                job_info = find_job_info(job_d)
                post = self._parse_job(job_info)
                if post:
                    jobs.append(post)
        return jobs, forward_cursor

    def _parse_job(self, job_info):
        if not job_info or len(job_info) < 29:
            return None

        # Avoid duplicates
        job_url = job_info[3][0][0] if job_info[3] else None
        if not job_url or job_url in self.seen_urls:
            return None
        self.seen_urls.add(job_url)

        title = job_info[0]
        company = job_info[1]
        location_str = job_info[2]
        city = location_str.split(',')[0] if location_str else None
        description = job_info[19]

        # Compute posted date
        date_posted = None
        try:
            days_ago_text = job_info[12] if len(job_info) > 12 else ""
            match = re.search(r'(\d+)\s+day', days_ago_text)
            if match:
                days_ago = int(match.group(1))
                date_posted = (datetime.now() - timedelta(days=days_ago)).date()
        except Exception:
            pass

        return JobPost(
            id=f"go-{job_info[28]}",
            title=title,
            company_name=company,
            location=Location(city=city),
            job_url=job_url,
            description=description,
            is_remote="remote" in description.lower(),
            emails=extract_emails_from_text(description),
            job_type=extract_job_type(description),
            salary=extract_salary(description),
            date_posted=date_posted,
        )
