"""Collect pull request metrics and store them in data/raw/pull_requests.csv."""

from __future__ import annotations

import logging
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config import get_settings
from src.github.graphql_client import GithubGraphQLClient
from src.io_utils import ensure_data_dirs, load_repositories, save_pull_requests
from src.logging_utils import setup_logging
from src.pr_collector import PullRequestCollector


def main() -> None:
    setup_logging()
    settings = get_settings()
    ensure_data_dirs(settings.data_raw_dir)

    repositories = load_repositories(settings.repositories_csv)
    if not repositories:
        logging.error("No repositories found. Run scripts/select_repos.py first.")
        return

    client = GithubGraphQLClient(settings)
    collector = PullRequestCollector(client, settings)

    logging.info("Collecting pull requests...")
    pull_requests = collector.collect_for_repositories(repositories)
    save_pull_requests(pull_requests, settings.pull_requests_csv)
    logging.info("Saved %s pull requests to %s", len(pull_requests), settings.pull_requests_csv)


if __name__ == "__main__":
    main()
