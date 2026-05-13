"""GitHub GraphQL client with rate limit handling."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
import time
from typing import Any

import requests

from ..config import Settings


class GithubGraphQLClient:
    """Thin wrapper around GitHub's GraphQL API."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._logger = logging.getLogger(self.__class__.__name__)
        self._endpoint = "https://api.github.com/graphql"

    def execute(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        """Execute a GraphQL query with basic error handling and retry logic."""

        max_retries = 5
        retry_wait = 10

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self._endpoint,
                    json={"query": query, "variables": variables},
                    headers={
                        "Authorization": f"Bearer {self._settings.github_token}",
                        "Accept": "application/vnd.github+json",
                    },
                    timeout=60,
                )

                # Retry on 502, 503, 504 (server errors)
                if response.status_code in (502, 503, 504):
                    if attempt < max_retries - 1:
                        self._logger.warning(
                            "API returned %s. Retrying in %s seconds (attempt %s/%s)...",
                            response.status_code,
                            retry_wait,
                            attempt + 1,
                            max_retries,
                        )
                        time.sleep(retry_wait)
                        retry_wait += 10  # Linear backoff: 10, 20, 30, 40
                        continue
                    else:
                        raise RuntimeError(
                            f"GitHub API error: {response.status_code} - {response.text}"
                        )

                if response.status_code != 200:
                    raise RuntimeError(
                        f"GitHub API error: {response.status_code} - {response.text}"
                    )

                payload = response.json()
                if payload.get("errors"):
                    raise RuntimeError(f"GraphQL errors: {payload['errors']}")

                data = payload.get("data") or {}
                self._handle_rate_limit(data.get("rateLimit"))
                return data

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    self._logger.warning(
                        "Request failed: %s. Retrying in %s seconds (attempt %s/%s)...",
                        str(e),
                        retry_wait,
                        attempt + 1,
                        max_retries,
                    )
                    time.sleep(retry_wait)
                    retry_wait += 10
                else:
                    raise

    def _handle_rate_limit(self, rate_limit: dict[str, Any] | None) -> None:
        if not rate_limit:
            return

        remaining = rate_limit.get("remaining", 0)
        reset_at = rate_limit.get("resetAt")

        if remaining <= self._settings.rate_limit_threshold:
            wait_seconds = self._seconds_until_reset(reset_at)
            if wait_seconds > 0:
                self._logger.warning(
                    "Rate limit low (%s). Waiting %s seconds...",
                    remaining,
                    wait_seconds,
                )
                time.sleep(wait_seconds)

    @staticmethod
    def _seconds_until_reset(reset_at: str | None) -> int:
        if not reset_at:
            return 0
        if reset_at.endswith("Z"):
            reset_at = reset_at.replace("Z", "+00:00")
        reset_time = datetime.fromisoformat(reset_at).astimezone(timezone.utc)
        now = datetime.now(timezone.utc)
        return max(0, int((reset_time - now).total_seconds()) + 1)
