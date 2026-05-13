import argparse
import csv
import math
import os
import re
import shutil
import subprocess
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median, stdev

REPO_ROOT = Path(__file__).resolve().parent
INPUT_REPOS_CSV = REPO_ROOT / "repos_java_1000.csv"
CLONES_DIR = REPO_ROOT / "clones"
CK_DIR = REPO_ROOT / "ck"
CK_JAR = CK_DIR / "ck.jar"
CK_JAR_URLS = [
    "https://repo1.maven.org/maven2/com/github/mauricioaniche/ck/0.7.0/ck-0.7.0-jar-with-dependencies.jar",
    "https://repo1.maven.org/maven2/com/github/mauricioaniche/ck/0.6.4/ck-0.6.4-jar-with-dependencies.jar",
]
OUTPUT_CSV_DEFAULT = REPO_ROOT / "medicoes_ck_1_repo.csv"


@dataclass
class RepoSelection:
    name_with_owner: str
    url: str
    stars: int
    releases_total: int
    repo_age_years: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Clona 1 repositório Java a partir de repos_java_1000.csv, executa CK, "
            "conta LOC/comentários e gera CSV sumarizado."
        )
    )
    parser.add_argument(
        "--repos-csv",
        type=Path,
        default=INPUT_REPOS_CSV,
        help="CSV de entrada com os repositórios (default: repos_java_1000.csv).",
    )
    parser.add_argument(
        "--repo",
        type=str,
        default="",
        help="Nome exato owner/repo para selecionar (ex.: iluwatar/java-design-patterns).",
    )
    parser.add_argument(
        "--index",
        type=int,
        default=0,
        help="Índice (0-based) no CSV se --repo não for informado.",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=OUTPUT_CSV_DEFAULT,
        help="Arquivo CSV de saída consolidada.",
    )
    parser.add_argument(
        "--ck-jar",
        type=Path,
        default=CK_JAR,
        help="Caminho para o arquivo ck.jar.",
    )
    parser.add_argument(
        "--force-reclone",
        action="store_true",
        help="Remove clone existente antes de clonar novamente.",
    )
    parser.add_argument(
        "--skip-ck",
        action="store_true",
        help="Pula execução do CK (útil para testar somente clone + LOC/comentários).",
    )
    return parser.parse_args()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def run_command(command: list[str], cwd: Path | None = None) -> None:
    result = subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            "Comando falhou: "
            + " ".join(command)
            + "\nSTDOUT:\n"
            + result.stdout
            + "\nSTDERR:\n"
            + result.stderr
        )


def read_repo_list(csv_path: Path) -> list[RepoSelection]:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV não encontrado: {csv_path}")

    rows: list[RepoSelection] = []
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(
                RepoSelection(
                    name_with_owner=row.get("nameWithOwner", "").strip(),
                    url=row.get("url", "").strip(),
                    stars=int(float(row.get("stars", "0") or 0)),
                    releases_total=int(float(row.get("releases_total", "0") or 0)),
                    repo_age_years=float(row.get("repo_age_years", "0") or 0),
                )
            )
    return rows


def select_repo(rows: list[RepoSelection], repo_name: str, index: int) -> RepoSelection:
    if repo_name:
        for row in rows:
            if row.name_with_owner.lower() == repo_name.lower():
                return row
        raise ValueError(f"Repositório não encontrado no CSV: {repo_name}")

    if index < 0 or index >= len(rows):
        raise IndexError(f"Índice fora da faixa: {index} (total: {len(rows)})")

    return rows[index]


def safe_repo_dir_name(name_with_owner: str) -> str:
    return name_with_owner.replace("/", "__")


def clone_repo(repo: RepoSelection, clones_dir: Path, force_reclone: bool) -> Path:
    ensure_dir(clones_dir)
    repo_dir = clones_dir / safe_repo_dir_name(repo.name_with_owner)

    if repo_dir.exists() and force_reclone:
        shutil.rmtree(repo_dir)

    if repo_dir.exists():
        print(f"Clone já existe: {repo_dir}")
        return repo_dir

    print(f"Clonando {repo.name_with_owner}...")
    run_command(["git", "clone", "--depth", "1", repo.url, str(repo_dir)])
    return repo_dir


def download_ck_if_needed(ck_jar: Path) -> None:
    if ck_jar.exists():
        return

    ensure_dir(ck_jar.parent)
    print("Baixando CK jar...")

    last_error: Exception | None = None
    for url in CK_JAR_URLS:
        try:
            urllib.request.urlretrieve(url, ck_jar)
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc

    raise RuntimeError(
        "Não foi possível baixar o CK jar a partir das URLs conhecidas. "
        f"Último erro: {last_error}"
    )


@dataclass
class LocStats:
    java_files: int
    loc_total: int
    comment_lines: int


def count_loc_and_comments(repo_dir: Path) -> LocStats:
    java_files = 0
    loc_total = 0
    comment_lines = 0

    for path in repo_dir.rglob("*.java"):
        if "/.git/" in path.as_posix():
            continue

        java_files += 1
        in_block_comment = False

        with path.open("r", encoding="utf-8", errors="ignore") as f:
            for raw_line in f:
                line = raw_line.rstrip("\n")
                stripped = line.strip()

                if not stripped:
                    continue

                loc_total += 1

                i = 0
                line_has_comment = False
                while i < len(line):
                    if in_block_comment:
                        line_has_comment = True
                        end = line.find("*/", i)
                        if end == -1:
                            i = len(line)
                        else:
                            in_block_comment = False
                            i = end + 2
                        continue

                    start_block = line.find("/*", i)
                    start_line = line.find("//", i)

                    if start_line != -1 and (start_block == -1 or start_line < start_block):
                        line_has_comment = True
                        break

                    if start_block != -1:
                        line_has_comment = True
                        end = line.find("*/", start_block + 2)
                        if end == -1:
                            in_block_comment = True
                            break
                        i = end + 2
                        continue

                    break

                if line_has_comment:
                    comment_lines += 1

    return LocStats(java_files=java_files, loc_total=loc_total, comment_lines=comment_lines)


@dataclass
class CkSummary:
    classes_analyzed: int
    cbo_mean: float
    cbo_median: float
    cbo_stddev: float
    dit_mean: float
    dit_median: float
    dit_stddev: float
    lcom_mean: float
    lcom_median: float
    lcom_stddev: float


def normalize_col_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def summarize_metric(values: list[float]) -> tuple[float, float, float]:
    if not values:
        return math.nan, math.nan, math.nan
    if len(values) == 1:
        v = values[0]
        return v, v, 0.0
    return mean(values), median(values), stdev(values)


def run_ck_and_summarize(repo_dir: Path, ck_jar: Path, output_base_dir: Path) -> CkSummary:
    repo_key = safe_repo_dir_name(repo_dir.name)
    ck_output_dir = output_base_dir / repo_key
    ensure_dir(ck_output_dir)

    command = [
        "java",
        "-jar",
        str(ck_jar),
        str(repo_dir),
        "false",
        "0",
        "false",
        str(ck_output_dir),
    ]
    print("Executando CK...")
    run_command(command)

    class_csv_candidates = [
        ck_output_dir / "class.csv",
        output_base_dir / f"{repo_key}class.csv",
        output_base_dir / "class.csv",
    ]
    class_csv = next((p for p in class_csv_candidates if p.exists()), None)
    if class_csv is None:
        raise FileNotFoundError(
            "Arquivo class.csv não encontrado. "
            f"Caminhos tentados: {[str(p) for p in class_csv_candidates]}"
        )

    cbo_values: list[float] = []
    dit_values: list[float] = []
    lcom_values: list[float] = []

    with class_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise RuntimeError("class.csv sem cabeçalho.")

        normalized = {normalize_col_name(col): col for col in reader.fieldnames}
        cbo_col = normalized.get("cbo")
        dit_col = normalized.get("dit")
        lcom_col = normalized.get("lcom")

        if not cbo_col or not dit_col or not lcom_col:
            raise RuntimeError(
                "Não foi possível identificar colunas CBO/DIT/LCOM em class.csv. "
                f"Colunas encontradas: {reader.fieldnames}"
            )

        for row in reader:
            try:
                cbo_values.append(float(row.get(cbo_col, "") or 0))
                dit_values.append(float(row.get(dit_col, "") or 0))
                lcom_values.append(float(row.get(lcom_col, "") or 0))
            except ValueError:
                continue

    cbo_mean, cbo_median, cbo_stddev = summarize_metric(cbo_values)
    dit_mean, dit_median, dit_stddev = summarize_metric(dit_values)
    lcom_mean, lcom_median, lcom_stddev = summarize_metric(lcom_values)

    return CkSummary(
        classes_analyzed=len(cbo_values),
        cbo_mean=cbo_mean,
        cbo_median=cbo_median,
        cbo_stddev=cbo_stddev,
        dit_mean=dit_mean,
        dit_median=dit_median,
        dit_stddev=dit_stddev,
        lcom_mean=lcom_mean,
        lcom_median=lcom_median,
        lcom_stddev=lcom_stddev,
    )


def write_summary_csv(
    output_csv: Path,
    repo: RepoSelection,
    loc_stats: LocStats,
    ck_summary: CkSummary | None,
) -> None:
    ensure_dir(output_csv.parent)

    fieldnames = [
        "repo",
        "url",
        "stars",
        "releases_total",
        "repo_age_years",
        "java_files",
        "loc_total",
        "comment_lines",
        "classes_analyzed",
        "cbo_mean",
        "cbo_median",
        "cbo_stddev",
        "dit_mean",
        "dit_median",
        "dit_stddev",
        "lcom_mean",
        "lcom_median",
        "lcom_stddev",
    ]

    def val(x: float | int | str | None) -> str | float | int:
        if x is None:
            return ""
        if isinstance(x, float) and math.isnan(x):
            return ""
        return x

    row = {
        "repo": repo.name_with_owner,
        "url": repo.url,
        "stars": repo.stars,
        "releases_total": repo.releases_total,
        "repo_age_years": repo.repo_age_years,
        "java_files": loc_stats.java_files,
        "loc_total": loc_stats.loc_total,
        "comment_lines": loc_stats.comment_lines,
        "classes_analyzed": val(ck_summary.classes_analyzed if ck_summary else None),
        "cbo_mean": val(ck_summary.cbo_mean if ck_summary else None),
        "cbo_median": val(ck_summary.cbo_median if ck_summary else None),
        "cbo_stddev": val(ck_summary.cbo_stddev if ck_summary else None),
        "dit_mean": val(ck_summary.dit_mean if ck_summary else None),
        "dit_median": val(ck_summary.dit_median if ck_summary else None),
        "dit_stddev": val(ck_summary.dit_stddev if ck_summary else None),
        "lcom_mean": val(ck_summary.lcom_mean if ck_summary else None),
        "lcom_median": val(ck_summary.lcom_median if ck_summary else None),
        "lcom_stddev": val(ck_summary.lcom_stddev if ck_summary else None),
    }

    with output_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(row)


def main() -> None:
    args = parse_args()

    rows = read_repo_list(args.repos_csv)
    repo = select_repo(rows, args.repo, args.index)

    print(f"Selecionado: {repo.name_with_owner}")
    repo_dir = clone_repo(repo, CLONES_DIR, args.force_reclone)

    loc_stats = count_loc_and_comments(repo_dir)
    print(
        "LOC/comentários: "
        f"java_files={loc_stats.java_files}, "
        f"loc_total={loc_stats.loc_total}, "
        f"comment_lines={loc_stats.comment_lines}"
    )

    ck_summary: CkSummary | None = None
    if args.skip_ck:
        print("CK pulado por --skip-ck")
    else:
        download_ck_if_needed(args.ck_jar)
        ck_summary = run_ck_and_summarize(repo_dir, args.ck_jar, REPO_ROOT / "ck_output")
        print(
            "CK: "
            f"classes={ck_summary.classes_analyzed}, "
            f"CBO(mean)={ck_summary.cbo_mean:.4f}, "
            f"DIT(mean)={ck_summary.dit_mean:.4f}, "
            f"LCOM(mean)={ck_summary.lcom_mean:.4f}"
        )

    write_summary_csv(args.output_csv, repo, loc_stats, ck_summary)
    print(f"CSV gerado: {args.output_csv}")


if __name__ == "__main__":
    main()
