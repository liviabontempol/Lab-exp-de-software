"""I/O utilities for reading and writing datasets."""

from __future__ import annotations

from pathlib import Path
import pandas as pd

from .models import PullRequestInfo, RepoInfo


def ensure_data_dirs(path: Path) -> None:
    """Ensure output directories exist."""

    path.mkdir(parents=True, exist_ok=True)


def save_repositories(repositories: list[RepoInfo], output_path: Path) -> None:
    """Persist selected repositories to CSV."""

    data = [repo.to_dict() for repo in repositories]
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)


def save_pull_requests(pull_requests: list[PullRequestInfo], output_path: Path) -> None:
    """Persist pull request metrics to CSV."""

    data = [pr.to_dict() for pr in pull_requests]
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)


def load_repositories(input_path: Path) -> list[RepoInfo]:
    """Load repository list from CSV."""

    df = pd.read_csv(input_path)
    repositories: list[RepoInfo] = []
    for _, row in df.iterrows():
        repositories.append(
            RepoInfo(
                repo_name=str(row["repo_name"]),
                owner=str(row["owner"]),
                language=str(row.get("language", "")),
                stars=int(row.get("stars", 0)),
                total_prs=int(row.get("total_prs", 0)),
                url=str(row.get("url", "")),
            )
        )
    return repositories
