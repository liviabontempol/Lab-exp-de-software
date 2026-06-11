"""Pull request collection and metrics extraction."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
import time

try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover - fallback when tqdm is unavailable
    def tqdm(iterable, **_kwargs):
        return iterable

from .config import Settings
from .github.graphql_client import GithubGraphQLClient
from .github.queries import PULL_REQUESTS_QUERY
from .models import RepoInfo


class PullRequestCollector:
    """Collect pull request metrics for selected repositories."""

    def __init__(self, client: GithubGraphQLClient, settings: Settings) -> None:
        self._client = client
        self._settings = settings
        self._logger = logging.getLogger(self.__class__.__name__)

    def collect_for_repositories(self, repositories: list[RepoInfo]) -> list[dict]:
        """Collect pull request metrics from a list of repositories."""

        collected: list[dict] = []

        for repo in tqdm(repositories, desc="Collecting PRs"):
            self._logger.info("Collecting PRs for %s/%s", repo.owner, repo.repo_name)
            collected.extend(self._collect_for_repository(repo))

        return collected

    def _collect_for_repository(self, repo: RepoInfo) -> list[dict]:
        items: list[PullRequestInfo] = []
        cursor: str | None = None
        has_next = True
        page_size = self._settings.pr_page_size

        while has_next:
            data = self._execute_pr_query(repo, page_size, cursor)
            repository = data.get("repository")
            if not repository:
                break

            pr_data = repository["pullRequests"]
            for node in pr_data.get("nodes", []):
                pr = self._to_pull_request(repo, node)
                if pr:
                    items.append(pr)

            page_info = pr_data["pageInfo"]
            has_next = page_info["hasNextPage"]
            cursor = page_info["endCursor"]
            
            if has_next:
                time.sleep(0.5)

        return items

    def _execute_pr_query(self, repo: RepoInfo, page_size: int, cursor: str | None) -> dict:
        current_page_size = page_size

        while True:
            variables = {
                "owner": repo.owner,
                "name": repo.repo_name,
                "first": current_page_size,
                "after": cursor,
            }

            try:
                return self._client.execute(PULL_REQUESTS_QUERY, variables)
            except RuntimeError as exc:
                message = str(exc).lower()
                retriable = (
                    "timeout" in message
                    or "something went wrong" in message
                    or "exceeded" in message
                    or "complexity" in message
                )

                if retriable and current_page_size > 1:
                    reduced = max(1, current_page_size // 2)
                    self._logger.warning(
                        "PR query too heavy for %s/%s at page size %s; retrying with %s.",
                        repo.owner,
                        repo.repo_name,
                        current_page_size,
                        reduced,
                    )
                    current_page_size = reduced
                    continue

                raise

    def _to_pull_request(self, repo: RepoInfo, node: dict) -> dict | None:
        reviews_info = node.get("reviews", {})
        reviews_count = reviews_info.get("totalCount", 0)
        if reviews_count == 0:
            return None

        created_at = node.get("createdAt")
        closed_at = node.get("closedAt")
        merged_at = node.get("mergedAt")
        end_at = closed_at or merged_at
        if not end_at or not created_at:
            return None

        duration_hours = self._duration_hours(created_at, end_at)
        if duration_hours < 1.0:
            return None

        additions = node.get("additions", 0) or 0
        deletions = node.get("deletions", 0) or 0
        changed_files = node.get("changedFiles", 0)

        # repository info
        repository = f"{repo.owner}/{repo.repo_name}"
        repository_url = getattr(repo, "url", None) or f"https://github.com/{repo.owner}/{repo.repo_name}"

        # description
        title = node.get("title")
        body = node.get("body") or ""
        body_length = len(body)

        # reviews details
        reviews_nodes = reviews_info.get("nodes", [])
        states_seen = []
        last_review_submitted_at = None
        last_state = None
        if reviews_nodes:
            # find last by submittedAt
            sorted_reviews = sorted(
                [r for r in reviews_nodes if r.get("submittedAt")],
                key=lambda r: r.get("submittedAt"),
            )
            if sorted_reviews:
                last = sorted_reviews[-1]
                last_review_submitted_at = last.get("submittedAt")
                last_state = last.get("state")
            states_seen = list({r.get("state") for r in reviews_nodes if r.get("state")})

        issue_comments = node.get("comments", {}).get("totalCount", 0)
        review_threads = node.get("reviewThreads", {}).get("totalCount", 0)

        interacoes_total = issue_comments + review_threads + reviews_count

        pr_dict = {
            "repository": repository,
            "repository_url": repository_url,
            "pr_number": node.get("number"),
            "pr_url": f"https://github.com/{repo.owner}/{repo.repo_name}/pull/{node.get('number')}",
            "pr_state": node.get("state"),
            "created_at": created_at,
            "merged_at": merged_at,
            "closed_at": closed_at,
            "tamanho_dos_prs": {
                "additions": additions,
                "deletions": deletions,
                "changed_files": changed_files,
                "total_changes": additions + deletions,
            },
            "tempo_de_analise_dos_prs": {
                "seconds": int(duration_hours * 3600),
                "hours": round(duration_hours, 2),
            },
            "interacoes_nos_prs": {
                "issue_comments": issue_comments,
                "review_comments": 0,
                "review_threads": review_threads,
                "reviews": reviews_count,
                "total_interactions": interacoes_total,
            },
            "descricao_dos_prs": {
                "title": title,
                "body": body,
                "body_length": body_length,
            },
            "numero_de_revisoes_realizadas": reviews_count,
            "feedback_final_das_revisoes": {
                "final_state": last_state,
                "states_seen": states_seen,
                "last_review_submitted_at": last_review_submitted_at,
            },
        }

        return pr_dict

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
