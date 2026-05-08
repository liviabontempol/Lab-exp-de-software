"""Data models for repositories and pull requests."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RepoInfo:
    """Repository metadata used for selection and collection."""

    repo_name: str
    owner: str
    language: str
    stars: int
    total_prs: int
    url: str

    def to_dict(self) -> dict:
        """Convert repository info to a serializable dictionary."""

        return {
            "repo_name": self.repo_name,
            "owner": self.owner,
            "language": self.language,
            "stars": self.stars,
            "total_prs": self.total_prs,
            "url": self.url,
        }


@dataclass(frozen=True)
class PullRequestInfo:
    """Pull request metrics extracted from GitHub."""

    repo_name: str
    pr_number: int
    state: str
    changed_files: int
    additions: int
    deletions: int
    created_at: str
    closed_at: str | None
    merged_at: str | None
    review_duration_hours: float
    body_length: int
    participants_count: int
    comments_count: int
    reviews_count: int

    def to_dict(self) -> dict:
        """Convert pull request info to a serializable dictionary."""

        return {
            "repo_name": self.repo_name,
            "pr_number": self.pr_number,
            "state": self.state,
            "changed_files": self.changed_files,
            "additions": self.additions,
            "deletions": self.deletions,
            "created_at": self.created_at,
            "closed_at": self.closed_at,
            "merged_at": self.merged_at,
            "review_duration_hours": self.review_duration_hours,
            "body_length": self.body_length,
            "participants_count": self.participants_count,
            "comments_count": self.comments_count,
            "reviews_count": self.reviews_count,
        }
