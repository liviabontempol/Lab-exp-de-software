"""Prepare processed datasets for BI dashboards (Lab following Lab03).

This script generates BI-friendly CSV files from raw datasets:
- data/raw/repositories.csv (required)
- data/raw/pull_requests.csv (optional, generated after PR collection)

Outputs are written to data/processed/bi/.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

import pandas as pd


@dataclass(frozen=True)
class Paths:
    raw_dir: Path
    processed_bi_dir: Path
    repositories_csv: Path
    pull_requests_csv: Path
    example_pr_json: Path


def _base_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def _build_paths() -> Paths:
    base_dir = _base_dir()
    raw_dir = base_dir / "data" / "raw"
    processed_bi_dir = base_dir / "data" / "processed" / "bi"
    return Paths(
        raw_dir=raw_dir,
        processed_bi_dir=processed_bi_dir,
        repositories_csv=raw_dir / "repositories.csv",
        pull_requests_csv=raw_dir / "pull_requests.csv",
        example_pr_json=raw_dir / "example_pull_request.json",
    )


def _safe_json(value: object) -> dict:
    if isinstance(value, dict):
        return value
    if value is None:
        return {}
    if isinstance(value, float) and pd.isna(value):
        return {}
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return {}
        try:
            decoded = json.loads(value)
            return decoded if isinstance(decoded, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def _bucket_total_changes(total_changes: float | int) -> str:
    value = float(total_changes or 0)
    if value <= 50:
        return "Ate 50"
    if value <= 200:
        return "51-200"
    if value <= 500:
        return "201-500"
    return "Acima de 500"


def _bucket_review_hours(hours: float | int) -> str:
    value = float(hours or 0)
    if value < 24:
        return "<24h"
    if value < 72:
        return "24-72h"
    if value < 168:
        return "3-7 dias"
    return ">=7 dias"


def _load_repositories(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo obrigatorio nao encontrado: {path}")

    repos = pd.read_csv(path)
    expected = {"repo_name", "owner", "language", "stars", "total_prs", "url"}
    missing = expected - set(repos.columns)
    if missing:
        raise ValueError(f"repositories.csv sem colunas esperadas: {sorted(missing)}")

    repos = repos.copy()
    repos["repository"] = repos["owner"].astype(str) + "/" + repos["repo_name"].astype(str)
    repos["language"] = repos["language"].fillna("Unknown")
    repos["stars"] = pd.to_numeric(repos["stars"], errors="coerce").fillna(0).astype(int)
    repos["total_prs"] = pd.to_numeric(repos["total_prs"], errors="coerce").fillna(0).astype(int)

    return repos


def _load_pull_requests(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()

    prs = pd.read_csv(path)
    if prs.empty:
        return prs

    nested_cols = [
        "tamanho_dos_prs",
        "tempo_de_analise_dos_prs",
        "interacoes_nos_prs",
        "descricao_dos_prs",
        "feedback_final_das_revisoes",
    ]
    for col in nested_cols:
        if col not in prs.columns:
            prs[col] = "{}"

    size_df = prs["tamanho_dos_prs"].map(_safe_json).apply(pd.Series)
    time_df = prs["tempo_de_analise_dos_prs"].map(_safe_json).apply(pd.Series)
    interactions_df = prs["interacoes_nos_prs"].map(_safe_json).apply(pd.Series)
    desc_df = prs["descricao_dos_prs"].map(_safe_json).apply(pd.Series)
    feedback_df = prs["feedback_final_das_revisoes"].map(_safe_json).apply(pd.Series)

    flat = pd.DataFrame()
    flat["repository"] = prs.get("repository")
    flat["repository_url"] = prs.get("repository_url")
    flat["pr_number"] = prs.get("pr_number")
    flat["pr_url"] = prs.get("pr_url")
    flat["pr_state"] = prs.get("pr_state")
    flat["created_at"] = prs.get("created_at")
    flat["merged_at"] = prs.get("merged_at")
    flat["closed_at"] = prs.get("closed_at")
    flat["additions"] = pd.to_numeric(size_df.get("additions"), errors="coerce").fillna(0).astype(int)
    flat["deletions"] = pd.to_numeric(size_df.get("deletions"), errors="coerce").fillna(0).astype(int)
    flat["changed_files"] = pd.to_numeric(size_df.get("changed_files"), errors="coerce").fillna(0).astype(int)
    flat["total_changes"] = pd.to_numeric(size_df.get("total_changes"), errors="coerce").fillna(0).astype(int)
    flat["review_duration_hours"] = (
        pd.to_numeric(time_df.get("hours"), errors="coerce").fillna(0).round(2)
    )
    flat["issue_comments"] = pd.to_numeric(interactions_df.get("issue_comments"), errors="coerce").fillna(0).astype(int)
    flat["review_comments"] = pd.to_numeric(interactions_df.get("review_comments"), errors="coerce").fillna(0).astype(int)
    flat["review_threads"] = pd.to_numeric(interactions_df.get("review_threads"), errors="coerce").fillna(0).astype(int)
    flat["reviews"] = pd.to_numeric(interactions_df.get("reviews"), errors="coerce").fillna(0).astype(int)
    flat["total_interactions"] = (
        pd.to_numeric(interactions_df.get("total_interactions"), errors="coerce").fillna(0).astype(int)
    )
    flat["title"] = desc_df.get("title").fillna("")
    flat["body_length"] = pd.to_numeric(desc_df.get("body_length"), errors="coerce").fillna(0).astype(int)
    flat["final_review_state"] = feedback_df.get("final_state").fillna("UNKNOWN")
    flat["last_review_submitted_at"] = feedback_df.get("last_review_submitted_at")

    repo_parts = flat["repository"].fillna("/").astype(str).str.split("/", n=1, expand=True)
    flat["owner"] = repo_parts[0].fillna("")
    flat["repo_name"] = repo_parts[1].fillna("")

    flat["created_at"] = pd.to_datetime(flat["created_at"], errors="coerce", utc=True)
    flat["merged_at"] = pd.to_datetime(flat["merged_at"], errors="coerce", utc=True)
    flat["closed_at"] = pd.to_datetime(flat["closed_at"], errors="coerce", utc=True)

    flat["created_date"] = flat["created_at"].dt.date.astype("string")
    flat["created_year_month"] = flat["created_at"].dt.to_period("M").astype("string")
    flat["size_bucket"] = flat["total_changes"].map(_bucket_total_changes)
    flat["review_time_bucket"] = flat["review_duration_hours"].map(_bucket_review_hours)

    return flat


def _write_csv(df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)


def _build_repo_aggregates(repos: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    overall = pd.DataFrame(
        {
            "kpi": [
                "total_repositories",
                "total_languages",
                "avg_stars",
                "median_stars",
                "avg_total_prs",
                "median_total_prs",
            ],
            "value": [
                int(repos["repository"].nunique()),
                int(repos["language"].nunique()),
                round(float(repos["stars"].mean()), 2),
                round(float(repos["stars"].median()), 2),
                round(float(repos["total_prs"].mean()), 2),
                round(float(repos["total_prs"].median()), 2),
            ],
        }
    )

    by_language = (
        repos.groupby("language", as_index=False)
        .agg(
            repositories=("repository", "nunique"),
            avg_stars=("stars", "mean"),
            median_stars=("stars", "median"),
            avg_total_prs=("total_prs", "mean"),
            median_total_prs=("total_prs", "median"),
        )
        .sort_values("repositories", ascending=False)
    )

    by_language[["avg_stars", "median_stars", "avg_total_prs", "median_total_prs"]] = (
        by_language[["avg_stars", "median_stars", "avg_total_prs", "median_total_prs"]].round(2)
    )

    return overall, by_language


def _build_pr_aggregates(prs: pd.DataFrame) -> dict[str, pd.DataFrame]:
    if prs.empty:
        return {
            "fact_pull_requests": prs,
            "kpi_pull_requests": pd.DataFrame(),
            "rq_review_time_by_language": pd.DataFrame(),
            "rq_size_vs_review_time": pd.DataFrame(),
            "rq_interactions_by_feedback": pd.DataFrame(),
            "rq_time_series_monthly": pd.DataFrame(),
        }

    kpi = pd.DataFrame(
        {
            "kpi": [
                "total_pull_requests",
                "median_review_duration_hours",
                "avg_review_duration_hours",
                "median_total_changes",
                "avg_total_changes",
                "median_total_interactions",
                "avg_total_interactions",
            ],
            "value": [
                int(len(prs)),
                round(float(prs["review_duration_hours"].median()), 2),
                round(float(prs["review_duration_hours"].mean()), 2),
                round(float(prs["total_changes"].median()), 2),
                round(float(prs["total_changes"].mean()), 2),
                round(float(prs["total_interactions"].median()), 2),
                round(float(prs["total_interactions"].mean()), 2),
            ],
        }
    )

    rq1 = (
        prs.groupby("language", as_index=False)
        .agg(
            prs_count=("pr_number", "count"),
            median_review_duration_hours=("review_duration_hours", "median"),
            mean_review_duration_hours=("review_duration_hours", "mean"),
            p25_review_duration_hours=("review_duration_hours", lambda s: s.quantile(0.25)),
            p75_review_duration_hours=("review_duration_hours", lambda s: s.quantile(0.75)),
        )
        .sort_values("prs_count", ascending=False)
    )

    rq2 = (
        prs.groupby("size_bucket", as_index=False)
        .agg(
            prs_count=("pr_number", "count"),
            median_total_changes=("total_changes", "median"),
            median_review_duration_hours=("review_duration_hours", "median"),
            mean_review_duration_hours=("review_duration_hours", "mean"),
            median_total_interactions=("total_interactions", "median"),
        )
    )

    bucket_order = ["Ate 50", "51-200", "201-500", "Acima de 500"]
    rq2["size_bucket"] = pd.Categorical(rq2["size_bucket"], categories=bucket_order, ordered=True)
    rq2 = rq2.sort_values("size_bucket")
    rq2["size_bucket"] = rq2["size_bucket"].astype(str)

    rq3 = (
        prs.groupby("final_review_state", as_index=False)
        .agg(
            prs_count=("pr_number", "count"),
            median_reviews=("reviews", "median"),
            mean_reviews=("reviews", "mean"),
            median_total_interactions=("total_interactions", "median"),
            mean_total_interactions=("total_interactions", "mean"),
            median_review_duration_hours=("review_duration_hours", "median"),
        )
        .sort_values("prs_count", ascending=False)
    )

    rq4 = (
        prs.groupby("created_year_month", as_index=False)
        .agg(
            prs_count=("pr_number", "count"),
            median_review_duration_hours=("review_duration_hours", "median"),
            median_total_changes=("total_changes", "median"),
            median_total_interactions=("total_interactions", "median"),
        )
        .sort_values("created_year_month", ascending=True)
    )

    for frame in [rq1, rq2, rq3, rq4]:
        numeric_cols = frame.select_dtypes(include=["number"]).columns
        frame[numeric_cols] = frame[numeric_cols].round(2)

    return {
        "fact_pull_requests": prs,
        "kpi_pull_requests": kpi,
        "rq_review_time_by_language": rq1,
        "rq_size_vs_review_time": rq2,
        "rq_interactions_by_feedback": rq3,
        "rq_time_series_monthly": rq4,
    }


def _attach_language(prs: pd.DataFrame, repos: pd.DataFrame) -> pd.DataFrame:
    if prs.empty:
        return prs

    cols = ["repository", "language"]
    repo_lang = repos[cols].drop_duplicates()
    merged = prs.merge(repo_lang, on="repository", how="left")
    merged["language"] = merged["language"].fillna("Unknown")
    return merged


def _create_example_schema(output_dir: Path, example_path: Path) -> None:
    if not example_path.exists():
        return

    with example_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    flat = {
        "repository": data.get("repository"),
        "pr_number": data.get("pr_number"),
        "pr_state": data.get("pr_state"),
        "created_at": data.get("created_at"),
        "merged_at": data.get("merged_at"),
        "closed_at": data.get("closed_at"),
        "additions": data.get("tamanho_dos_prs", {}).get("additions"),
        "deletions": data.get("tamanho_dos_prs", {}).get("deletions"),
        "changed_files": data.get("tamanho_dos_prs", {}).get("changed_files"),
        "total_changes": data.get("tamanho_dos_prs", {}).get("total_changes"),
        "review_duration_hours": data.get("tempo_de_analise_dos_prs", {}).get("hours"),
        "issue_comments": data.get("interacoes_nos_prs", {}).get("issue_comments"),
        "review_comments": data.get("interacoes_nos_prs", {}).get("review_comments"),
        "review_threads": data.get("interacoes_nos_prs", {}).get("review_threads"),
        "reviews": data.get("interacoes_nos_prs", {}).get("reviews"),
        "total_interactions": data.get("interacoes_nos_prs", {}).get("total_interactions"),
        "title": data.get("descricao_dos_prs", {}).get("title"),
        "body_length": data.get("descricao_dos_prs", {}).get("body_length"),
        "final_review_state": data.get("feedback_final_das_revisoes", {}).get("final_state"),
    }

    pd.DataFrame([flat]).to_csv(output_dir / "example_pr_flat_schema.csv", index=False)


def main() -> None:
    paths = _build_paths()
    paths.processed_bi_dir.mkdir(parents=True, exist_ok=True)

    repos = _load_repositories(paths.repositories_csv)
    prs = _load_pull_requests(paths.pull_requests_csv)
    prs = _attach_language(prs, repos)

    repo_kpis, repo_by_language = _build_repo_aggregates(repos)
    pr_outputs = _build_pr_aggregates(prs)

    _write_csv(repos, paths.processed_bi_dir / "fact_repositories.csv")
    _write_csv(repo_kpis, paths.processed_bi_dir / "kpi_repositories.csv")
    _write_csv(repo_by_language, paths.processed_bi_dir / "dataset_characterization_by_language.csv")

    for name, frame in pr_outputs.items():
        _write_csv(frame, paths.processed_bi_dir / f"{name}.csv")

    _create_example_schema(paths.processed_bi_dir, paths.example_pr_json)

    print("Arquivos BI gerados em:")
    print(paths.processed_bi_dir)
    print("- fact_repositories.csv")
    print("- kpi_repositories.csv")
    print("- dataset_characterization_by_language.csv")
    print("- fact_pull_requests.csv (se houver pull_requests.csv)")
    print("- kpi_pull_requests.csv (se houver pull_requests.csv)")
    print("- rq_review_time_by_language.csv (se houver pull_requests.csv)")
    print("- rq_size_vs_review_time.csv (se houver pull_requests.csv)")
    print("- rq_interactions_by_feedback.csv (se houver pull_requests.csv)")
    print("- rq_time_series_monthly.csv (se houver pull_requests.csv)")
    print("- example_pr_flat_schema.csv")


if __name__ == "__main__":
    main()
