"""Repository selection logic based on GitHub GraphQL search."""

from __future__ import annotations

import logging
import math
from typing import Iterable

from .config import Settings
from .github.graphql_client import GithubGraphQLClient
from .github.queries import SEARCH_REPOSITORIES_QUERY
from .models import RepoInfo


class RepoSelector:
    """Select repositories based on popularity and pull request activity."""

    def __init__(self, client: GithubGraphQLClient, settings: Settings) -> None:
        self._client = client
        self._settings = settings
        self._logger = logging.getLogger(self.__class__.__name__)

    def select_repositories(self) -> list[RepoInfo]:
        """Select repositories matching the criteria in the lab instructions."""

        per_language_target = math.ceil(
            self._settings.target_repo_count / len(self._settings.languages)
        )
        selected: list[RepoInfo] = []
        seen: set[str] = set()

        for language in self._settings.languages:
            self._logger.info("Selecting repositories for language: %s", language)
            selected.extend(
                self._collect_by_language(language, per_language_target, seen)
            )

        if len(selected) < self._settings.target_repo_count:
            remaining = self._settings.target_repo_count - len(selected)
            self._logger.info("Filling remaining %s repositories without language filter", remaining)
            selected.extend(self._collect_any_language(remaining, seen))

        return selected[: self._settings.target_repo_count]

    def _collect_by_language(
        self, language: str, target: int, seen: set[str]
    ) -> list[RepoInfo]:
        query = f"stars:>1 sort:stars language:{language}"
        return self._collect_from_search(query, target, seen)

    def _collect_any_language(self, target: int, seen: set[str]) -> list[RepoInfo]:
        query = "stars:>1 sort:stars"
        return self._collect_from_search(query, target, seen)

    def _collect_from_search(
        self, query: str, target: int, seen: set[str]
    ) -> list[RepoInfo]:
        collected: list[RepoInfo] = []
        cursor: str | None = None
        has_next = True

        while has_next and len(collected) < target:
            variables = {
                "query": query,
                "first": self._settings.search_page_size,
                "after": cursor,
            }
            data = self._client.execute(SEARCH_REPOSITORIES_QUERY, variables)
            search = data["search"]

            for node in self._extract_repository_nodes(search.get("nodes", [])):
                owner = node["owner"]["login"]
                name = node["name"]
                full_name = f"{owner}/{name}"
                if full_name in seen:
                    continue

                pr_count = node["pullRequests"]["totalCount"]
                if pr_count < self._settings.min_pr_count:
                    continue

                language = "Unknown"
                if node.get("primaryLanguage"):
                    language = node["primaryLanguage"].get("name") or "Unknown"

                repo = RepoInfo(
                    repo_name=name,
                    owner=owner,
                    language=language,
                    stars=node["stargazerCount"],
                    total_prs=pr_count,
                    url=node["url"],
                )
                collected.append(repo)
                seen.add(full_name)

                if len(collected) >= target:
                    break

            page_info = search["pageInfo"]
            has_next = page_info["hasNextPage"]
            cursor = page_info["endCursor"]

        return collected

    @staticmethod
    def _extract_repository_nodes(nodes: Iterable[dict]) -> list[dict]:
        """Normalize repository nodes from GraphQL search."""

        return [node for node in nodes if node is not None]
