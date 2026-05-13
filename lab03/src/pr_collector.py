"""Pull request collection and metrics extraction."""

from __future__ import annotations

from datetime import datetime, timezone
import logging

from tqdm import tqdm

from .config import Settings
from .github.graphql_client import GithubGraphQLClient
from .github.queries import PULL_REQUESTS_QUERY
from .models import PullRequestInfo, RepoInfo


class PullRequestCollector:
    """Collect pull request metrics for selected repositories."""

    def __init__(self, client: GithubGraphQLClient, settings: Settings) -> None:
        self._client = client
        self._settings = settings
        self._logger = logging.getLogger(self.__class__.__name__)

    def collect_for_repositories(self, repositories: list[RepoInfo]) -> list[PullRequestInfo]:
        """Collect pull request metrics from a list of repositories."""

        collected: list[PullRequestInfo] = []

        for repo in tqdm(repositories, desc="Collecting PRs"):
            self._logger.info("Collecting PRs for %s/%s", repo.owner, repo.repo_name)
            collected.extend(self._collect_for_repository(repo))

        return collected

    def _collect_for_repository(self, repo: RepoInfo) -> list[PullRequestInfo]:
        items: list[PullRequestInfo] = []
        cursor: str | None = None
        has_next = True

        while has_next:
            variables = {
                "owner": repo.owner,
                "name": repo.repo_name,
                "first": self._settings.pr_page_size,
                "after": cursor,
            }
            data = self._client.execute(PULL_REQUESTS_QUERY, variables)
            repository = data.get("repository")
            if not repository:
                break

            pr_data = repository["pullRequests"]
            for node in pr_data.get("nodes", []):
                pr = self._to_pull_request(repo.repo_name, node)
                if pr:
                    items.append(pr)

            page_info = pr_data["pageInfo"]
            has_next = page_info["hasNextPage"]
            cursor = page_info["endCursor"]

        return items

    def _to_pull_request(self, repo_name: str, node: dict) -> PullRequestInfo | None:
        reviews_count = node["reviews"]["totalCount"]
        if reviews_count == 0:
            return None

        created_at = node["createdAt"]
        closed_at = node.get("closedAt")
        merged_at = node.get("mergedAt")
        end_at = closed_at or merged_at
        if not end_at:
            return None

        duration_hours = self._duration_hours(created_at, end_at)
        if duration_hours < 1.0:
            return None

        body_length = len(node.get("bodyText") or "")

        return PullRequestInfo(
            repo_name=repo_name,
            pr_number=node["number"],
            state=node["state"],
            changed_files=node["changedFiles"],
            additions=node["additions"],
            deletions=node["deletions"],
            created_at=created_at,
            closed_at=closed_at,
            merged_at=merged_at,
            review_duration_hours=round(duration_hours, 2),
            body_length=body_length,
            participants_count=node["participants"]["totalCount"],
            comments_count=node["comments"]["totalCount"],
            reviews_count=reviews_count,
        )

    @staticmethod
    def _duration_hours(start: str, end: str) -> float:
        start_dt = PullRequestCollector._parse_datetime(start)
        end_dt = PullRequestCollector._parse_datetime(end)
        if not start_dt or not end_dt:
            return 0.0
        duration = end_dt - start_dt
        return duration.total_seconds() / 3600

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(value).astimezone(timezone.utc)
