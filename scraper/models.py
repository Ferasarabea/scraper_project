from dataclasses import dataclass
import pandas as pd

@dataclass
class Location:
    city: str = None
    state: str = None
    country: str = None

@dataclass
class JobPost:
    id: str
    title: str
    company_name: str
    location: Location
    job_url: str
    description: str
    is_remote: bool
    emails: list
    job_type: str
    date_posted: str = None
    salary: str = None


@dataclass
class ScraperInput:
    search_term: str
    location: str
    results_wanted: int
    hours_old: int
    is_remote: bool = False
    offset: int = 0
    google_search_term: str = None

@dataclass
class JobResponse:
    jobs: list

    def to_df(self):
        return pd.DataFrame([job.__dict__ for job in self.jobs])
