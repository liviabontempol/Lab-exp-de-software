"""Run repository selection and PR collection in sequence."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.collect_prs import main as collect_prs
from scripts.select_repos import main as select_repos


def main() -> None:
    select_repos()
    collect_prs()


if __name__ == "__main__":
    main()
