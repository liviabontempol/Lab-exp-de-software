"""Configuration and settings for Lab 03."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Project settings loaded from environment variables."""

    github_token: str
    base_dir: Path
    data_raw_dir: Path
    repositories_csv: Path
    pull_requests_csv: Path
    target_repo_count: int
    min_pr_count: int
    languages: list[str]
    search_page_size: int
    pr_page_size: int
    rate_limit_threshold: int


def get_settings() -> Settings:
    """Load settings from environment variables and defaults."""

    token = os.getenv("GITHUB_TOKEN") or os.getenv("API_TOKEN")
    if not token:
        raise ValueError("Missing GitHub token. Set GITHUB_TOKEN or API_TOKEN in .env.")

    base_dir = Path(__file__).resolve().parents[1]
    data_raw_dir = base_dir / "data" / "raw"

    return Settings(
        github_token=token,
        base_dir=base_dir,
        data_raw_dir=data_raw_dir,
        repositories_csv=data_raw_dir / "repositories.csv",
        pull_requests_csv=data_raw_dir / "pull_requests.csv",
        target_repo_count=200,
        min_pr_count=100,
        languages=["TypeScript", "Python", "JavaScript", "Java", "C#"],
        search_page_size=50,
        pr_page_size=100,
        rate_limit_threshold=10,
    )
