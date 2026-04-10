import csv
import os
import shutil
import subprocess
import stat
import time
from statistics import mean, median

from config import (
    CK_JAR_PATH,
    LIMIT_REPOS,
    QUALITY_CSV,
    REPOS_CSV,
    WORKDIR_CK_OUTPUT,
    WORKDIR_CLONES,
)


def _safe_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _summarize(values):
    clean = [v for v in values if v is not None]
    if not clean:
        return {"mean": "", "median": "", "std": ""}
    m = mean(clean)
    md = median(clean)
    if len(clean) == 1:
        return {"mean": round(m, 4), "median": round(md, 4), "std": 0.0}
    var = sum((x - m) ** 2 for x in clean) / (len(clean) - 1)
    return {"mean": round(m, 4), "median": round(md, 4), "std": round(var ** 0.5, 4)}


def _read_repos_csv(path):
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _repo_paths(name_with_owner):
    safe = name_with_owner.replace("/", "__")
    return (
        os.path.join(WORKDIR_CLONES, safe),
        os.path.join(WORKDIR_CK_OUTPUT, safe),
    )


def _handle_remove_readonly(func, path, _exc_info):
    os.chmod(path, stat.S_IWRITE)
    func(path)


def _remove_dir_robusto(path, tentativas=3):
    if not os.path.exists(path):
        return
    last_error = None
    for _ in range(tentativas):
        try:
            shutil.rmtree(path, onerror=_handle_remove_readonly)
            if not os.path.exists(path):
                return
        except Exception as e:
            last_error = e
        time.sleep(0.3)
    raise RuntimeError(f"Não foi possível limpar diretório '{path}'. Feche arquivos/terminals que usem essa pasta. {last_error}")


def _clone_repo(name_with_owner, target_dir):
    clone_url = f"https://github.com/{name_with_owner}.git"
    _remove_dir_robusto(target_dir)
    subprocess.run(
        ["git", "clone", "--depth", "1", clone_url, target_dir],
        check=True,
        capture_output=True,
        text=True,
    )


def _count_loc_and_comments(repo_dir):
    loc = 0
    comments = 0

    for root, _, files in os.walk(repo_dir):
        if any(skip in root for skip in [".git", "target", "build", "node_modules", ".idea"]):
            continue
        for fn in files:
            if not fn.endswith(".java"):
                continue
            p = os.path.join(root, fn)
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    in_block = False
                    for raw in f:
                        line = raw.strip()
                        if not line:
                            continue
                        if in_block:
                            comments += 1
                            if "*/" in line:
                                in_block = False
                            continue
                        if line.startswith("//"):
                            comments += 1
                            continue
                        if line.startswith("/*"):
                            comments += 1
                            if "*/" not in line:
                                in_block = True
                            continue
                        loc += 1
            except OSError:
                continue

    return loc, comments


def _run_ck(repo_dir, out_dir):
    _remove_dir_robusto(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    # Formato oficial do CK:
    # java -jar ck.jar <project dir> <useJars:true|false> <max files:0> <variablesAndFields:true|false> <output dir> [ignored dirs...]
    subprocess.run(
        [
            "java",
            "-jar",
            CK_JAR_PATH,
            repo_dir,
            "false",
            "0",
            "false",
            out_dir,
            # diretórios comuns que podem ser ignorados durante análise
            "target",
            "build",
            ".gradle",
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def _find_ck_class_csv(out_dir):
    candidates = ["class.csv", "class.csv.csv", "class_metrics.csv"]
    for root, _, files in os.walk(out_dir):
        for c in candidates:
            if c in files:
                return os.path.join(root, c)
    for root, _, files in os.walk(out_dir):
        for fn in files:
            if "class" in fn.lower() and fn.lower().endswith(".csv"):
                return os.path.join(root, fn)
    return None


def _load_ck_quality_summary(class_csv):
    cbo_vals, dit_vals, lcom_vals = [], [], []
    with open(class_csv, "r", encoding="utf-8", errors="ignore") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return None

    cols = {c.lower().strip(): c for c in rows[0].keys()}
    c_cbo = cols.get("cbo")
    c_dit = cols.get("dit")
    c_lcom = cols.get("lcom")
    if not (c_cbo and c_dit and c_lcom):
        return None

    for r in rows:
        cbo_vals.append(_safe_float(r.get(c_cbo)))
        dit_vals.append(_safe_float(r.get(c_dit)))
        lcom_vals.append(_safe_float(r.get(c_lcom)))

    return {
        "cbo": _summarize(cbo_vals),
        "dit": _summarize(dit_vals),
        "lcom": _summarize(lcom_vals),
    }


def executar_pipeline():
    os.makedirs(WORKDIR_CLONES, exist_ok=True)
    os.makedirs(WORKDIR_CK_OUTPUT, exist_ok=True)

    repos = _read_repos_csv(REPOS_CSV)[:LIMIT_REPOS]
    out_rows = []

    for i, repo in enumerate(repos, start=1):
        name = repo["nameWithOwner"]
        print(f"[{i}/{len(repos)}] Processando {name}")
        clone_dir, ck_dir = _repo_paths(name)

        base = {
            "nameWithOwner": name,
            "url": repo.get("url", ""),
            "stars": repo.get("stars", ""),
            "releases_total": repo.get("releases_total", ""),
            "repo_age_years": repo.get("repo_age_years", ""),
            "primaryLanguage": repo.get("primaryLanguage", "Java"),
            "loc": "",
            "comment_lines": "",
            "cbo_mean": "",
            "cbo_median": "",
            "cbo_std": "",
            "dit_mean": "",
            "dit_median": "",
            "dit_std": "",
            "lcom_mean": "",
            "lcom_median": "",
            "lcom_std": "",
            "status": "ok",
            "erro": "",
        }

        try:
            _clone_repo(name, clone_dir)
            loc, comments = _count_loc_and_comments(clone_dir)
            base["loc"] = loc
            base["comment_lines"] = comments

            _run_ck(clone_dir, ck_dir)
            class_csv = _find_ck_class_csv(ck_dir)
            if not class_csv:
                base["status"] = "erro"
                base["erro"] = "Arquivo de classes do CK não encontrado."
            else:
                s = _load_ck_quality_summary(class_csv)
                if not s:
                    base["status"] = "erro"
                    base["erro"] = "Colunas CBO/DIT/LCOM não encontradas no CSV do CK."
                else:
                    base["cbo_mean"] = s["cbo"]["mean"]
                    base["cbo_median"] = s["cbo"]["median"]
                    base["cbo_std"] = s["cbo"]["std"]
                    base["dit_mean"] = s["dit"]["mean"]
                    base["dit_median"] = s["dit"]["median"]
                    base["dit_std"] = s["dit"]["std"]
                    base["lcom_mean"] = s["lcom"]["mean"]
                    base["lcom_median"] = s["lcom"]["median"]
                    base["lcom_std"] = s["lcom"]["std"]
        except subprocess.CalledProcessError as e:
            base["status"] = "erro"
            base["erro"] = (e.stderr or e.stdout or str(e))[:500]
        except Exception as e:
            base["status"] = "erro"
            base["erro"] = str(e)[:500]
        finally:
            out_rows.append(base)

    with open(QUALITY_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        writer.writeheader()
        writer.writerows(out_rows)

    ok = sum(1 for r in out_rows if r["status"] == "ok")
    print(f"Finalizado. {ok}/{len(out_rows)} repositórios com métricas geradas.")
    print(f"Arquivo final: {QUALITY_CSV}")


if __name__ == "__main__":
    executar_pipeline()
