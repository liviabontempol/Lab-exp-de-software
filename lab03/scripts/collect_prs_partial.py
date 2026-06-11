"""Collect PRs for a small subset of repositories with incremental save (for pipeline validation)."""

from __future__ import annotations

import logging
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config import get_settings
from src.github.graphql_client import GithubGraphQLClient
from src.io_utils import ensure_data_dirs, load_repositories, append_pull_requests
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

    # Collect only first 10 repos (or customize via env)
    subset = repositories[:10]
    logging.info("Running partial collection for %d repositories", len(subset))

    client = GithubGraphQLClient(settings)
    collector = PullRequestCollector(client, settings)

    # Save to partial CSV
    output = settings.data_raw_dir / "pull_requests_partial.csv"
    
    # Collect each repo and save incrementally
    for i, repo in enumerate(subset, 1):
        logging.info("Collecting repo %d/%d: %s/%s", i, len(subset), repo.owner, repo.repo_name)
        try:
            pull_requests = collector._collect_for_repository(repo)
            if pull_requests:
                append_pull_requests(pull_requests, output)
                logging.info("Saved %d PRs from %s/%s", len(pull_requests), repo.owner, repo.repo_name)
        except Exception as e:
            logging.error("Failed to collect %s/%s: %s", repo.owner, repo.repo_name, e)
            continue

    logging.info("Partial collection complete. Check %s", output)


if __name__ == "__main__":
    main()
