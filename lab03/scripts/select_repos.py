"""Select repositories and store them in data/raw/repositories.csv."""

from __future__ import annotations

import logging
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config import get_settings
from src.github.graphql_client import GithubGraphQLClient
from src.io_utils import ensure_data_dirs, save_repositories
from src.logging_utils import setup_logging
from src.repo_selection import RepoSelector


def main() -> None:
    setup_logging()
    settings = get_settings()
    ensure_data_dirs(settings.data_raw_dir)

    client = GithubGraphQLClient(settings)
    selector = RepoSelector(client, settings)

    logging.info("Selecting repositories...")
    repositories = selector.select_repositories()
    save_repositories(repositories, settings.repositories_csv)
    logging.info("Saved %s repositories to %s", len(repositories), settings.repositories_csv)
    _print_repositories_by_language(repositories)


def _print_repositories_by_language(repositories: list) -> None:
    """Print a compact summary table grouped by language."""

    grouped: dict[str, list] = {}
    for repo in repositories:
        grouped.setdefault(repo.language, []).append(repo)

    header = f"{'Language':12} | {'Repos':>5} | {'Stars(avg)':>10} | {'PRs(avg)':>8} | Examples"
    print("\nRepository summary by language:")
    print(header)
    print("-" * len(header))

    for language in sorted(grouped.keys()):
        items = grouped[language]
        repo_count = len(items)
        avg_stars = sum(repo.stars for repo in items) / repo_count
        avg_prs = sum(repo.total_prs for repo in items) / repo_count
        examples = ", ".join(
            f"{repo.owner}/{repo.repo_name}" for repo in items[:3]
        )
        print(
            f"{language:12} | {repo_count:5d} | {avg_stars:10.0f} | {avg_prs:8.0f} | {examples}"
        )

    print("-" * len(header))


if __name__ == "__main__":
    main()
