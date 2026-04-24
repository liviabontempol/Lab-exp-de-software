import csv
import os
import shutil
import stat
import subprocess
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


def _validar_ck_jar() -> None:
    ck = CK_JAR_PATH
    if not ck or not os.path.isfile(ck):
        raise RuntimeError(
            f"CK_JAR_PATH inválido ou arquivo não encontrado: {ck!r}. "
            "Use o arquivo jar-with-dependencies gerado pelo Maven."
        )

    base = os.path.basename(ck).lower()
    if "javadoc" in base:
        raise RuntimeError("CK_JAR_PATH aponta para javadoc.jar.")
    if "sources" in base:
        raise RuntimeError("CK_JAR_PATH aponta para sources.jar.")
    if "jar-with-dependencies" not in base:
        print(
            "[AVISO] O arquivo não parece ser o fat jar do CK. "
            "Se der erro de execução, troque para o jar-with-dependencies."
        )


def _safe_float(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _summarize(values):
    clean = [v for v in values if v is not None]
    if not clean:
        return None

    m = mean(clean)
    md = median(clean)

    if len(clean) == 1:
        return {"mean": round(m, 4), "median": round(md, 4), "std": 0.0}

    var = sum((x - m) ** 2 for x in clean) / (len(clean) - 1)
    return {
        "mean": round(m, 4),
        "median": round(md, 4),
        "std": round(var ** 0.5, 4),
    }


def _read_csv_rows(path):
    if not os.path.exists(path):
        return []
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

    raise RuntimeError(
        f"Não foi possível limpar diretório '{path}'. "
        f"Feche arquivos/terminais que usem essa pasta. {last_error}"
    )


def _clone_repo(name_with_owner, target_dir):
    clone_url = f"https://github.com/{name_with_owner}.git"
    _remove_dir_robusto(target_dir)

    subprocess.run(
        [
            "git",
            "-c",
            "core.longpaths=true",
            "clone",
            "--depth",
            "1",
            clone_url,
            target_dir,
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def _count_loc_and_comments(repo_dir):
    loc = 0
    comments = 0

    for root, _, files in os.walk(repo_dir):
        if any(skip in root for skip in [".git", "target", "build", "node_modules", ".idea", ".gradle"]):
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


def _normalizar_cabecalhos_csv(keys):
    m = {}
    for k in keys:
        if k is None:
            continue
        nk = k.replace("\ufeff", "").strip().lower()
        m[nk] = k
    return m


def _load_ck_quality_summary(class_csv):
    cbo_vals, dit_vals, lcom_vals = [], [], []

    with open(class_csv, "r", encoding="utf-8-sig", errors="ignore") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        return None

    cols = _normalizar_cabecalhos_csv(rows[0].keys())
    c_cbo = cols.get("cbo")
    c_dit = cols.get("dit")
    c_lcom = cols.get("lcom") or cols.get("lcom*")

    if not (c_cbo and c_dit and c_lcom):
        return None

    for r in rows:
        cbo_vals.append(_safe_float(r.get(c_cbo)))
        dit_vals.append(_safe_float(r.get(c_dit)))
        lcom_vals.append(_safe_float(r.get(c_lcom)))

    s_cbo = _summarize(cbo_vals)
    s_dit = _summarize(dit_vals)
    s_lcom = _summarize(lcom_vals)

    if not s_cbo or not s_dit or not s_lcom:
        return None

    return {
        "cbo": s_cbo,
        "dit": s_dit,
        "lcom": s_lcom,
    }


def _deve_pular_antes(repo):
    lang = (repo.get("primaryLanguage") or "").strip().lower()
    if lang and lang != "java":
        return True

    nome = (repo.get("nameWithOwner") or "").lower()

    termos_ruins = [
        "awesome",
        "leetcode",
        "interview",
        "algorithm",
        "tutorial",
        "top-charts",
    ]

    if any(t in nome for t in termos_ruins):
        return True

    return False


def _tem_metricas_validas(row):
    metricas = [
        "cbo_mean", "cbo_median", "cbo_std",
        "dit_mean", "dit_median", "dit_std",
        "lcom_mean", "lcom_median", "lcom_std",
    ]
    return all(str(row.get(m, "")).strip() != "" for m in metricas)


def _carregar_existentes_ok(path):
    rows = _read_csv_rows(path)
    out = {}
    for row in rows:
        nome = (row.get("nameWithOwner") or "").strip()
        if not nome:
            continue

        status = (row.get("status") or "").strip().lower()
        if status == "ok" and _tem_metricas_validas(row):
            out[nome] = row

    return out


def _salvar_csv(path, rows):
    fieldnames = [
        "nameWithOwner",
        "url",
        "stars",
        "releases_total",
        "repo_age_years",
        "primaryLanguage",
        "loc",
        "comment_lines",
        "cbo_mean",
        "cbo_median",
        "cbo_std",
        "dit_mean",
        "dit_median",
        "dit_std",
        "lcom_mean",
        "lcom_median",
        "lcom_std",
        "status",
        "erro",
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        if rows:
            writer.writerows(rows)


def executar_pipeline():
    _validar_ck_jar()
    os.makedirs(WORKDIR_CLONES, exist_ok=True)
    os.makedirs(WORKDIR_CK_OUTPUT, exist_ok=True)

    repos = _read_csv_rows(REPOS_CSV)
    if not repos:
        raise RuntimeError(f"Nenhum repositório encontrado em {REPOS_CSV}")

    # só mantém os OK já válidos
    out_rows_map = _carregar_existentes_ok(QUALITY_CSV)
    ja_processados = set(out_rows_map.keys())

    print(f"Repos já válidos no CSV: {len(ja_processados)}")

    candidatos = []
    for repo in repos:
        nome = (repo.get("nameWithOwner") or "").strip()
        if not nome:
            continue
        if nome in ja_processados:
            continue
        candidatos.append(repo)

    if LIMIT_REPOS > 0:
        candidatos = candidatos[:LIMIT_REPOS]

    print(f"Repos pendentes nesta rodada: {len(candidatos)}")

    if not candidatos:
        print("Nada para processar.")
        return

    total = len(candidatos)
    novos_ok = 0

    for i, repo in enumerate(candidatos, start=1):
        name = (repo.get("nameWithOwner") or "").strip()
        print(f"[{i}/{total}] Processando {name}")

        clone_dir, ck_dir = _repo_paths(name)

        try:
            if _deve_pular_antes(repo):
                print("  -> pulado antes do clone")
                continue

            _clone_repo(name, clone_dir)

            loc, comments = _count_loc_and_comments(clone_dir)
            if loc < 500:
                print(f"  -> pulado por LOC baixo ({loc})")
                continue

            _run_ck(repo_dir=clone_dir, out_dir=ck_dir)

            class_csv = _find_ck_class_csv(ck_dir)
            if not class_csv:
                print("  -> class.csv não encontrado")
                continue

            ck_summary = _load_ck_quality_summary(class_csv)
            if not ck_summary:
                print("  -> métricas do CK inválidas ou ausentes")
                continue

            base = {
                "nameWithOwner": name,
                "url": repo.get("url", ""),
                "stars": repo.get("stars", ""),
                "releases_total": repo.get("releases_total", ""),
                "repo_age_years": repo.get("repo_age_years", ""),
                "primaryLanguage": repo.get("primaryLanguage", "Java"),
                "loc": loc,
                "comment_lines": comments,
                "cbo_mean": ck_summary["cbo"]["mean"],
                "cbo_median": ck_summary["cbo"]["median"],
                "cbo_std": ck_summary["cbo"]["std"],
                "dit_mean": ck_summary["dit"]["mean"],
                "dit_median": ck_summary["dit"]["median"],
                "dit_std": ck_summary["dit"]["std"],
                "lcom_mean": ck_summary["lcom"]["mean"],
                "lcom_median": ck_summary["lcom"]["median"],
                "lcom_std": ck_summary["lcom"]["std"],
                "status": "ok",
                "erro": "",
            }

            out_rows_map[name] = base
            novos_ok += 1

            # salva só os OK
            _salvar_csv(QUALITY_CSV, list(out_rows_map.values()))
            print("  -> OK")

        except subprocess.CalledProcessError as e:
            msg = (e.stderr or e.stdout or str(e))[:180]
            print(f"  -> erro subprocess, pulando: {msg}")
        except Exception as e:
            print(f"  -> erro, pulando: {str(e)[:180]}")
        finally:
            try:
                _remove_dir_robusto(clone_dir)
            except Exception as e:
                print(f"  -> erro ao apagar clone: {e}")

            try:
                _remove_dir_robusto(ck_dir)
            except Exception as e:
                print(f"  -> erro ao apagar saída CK: {e}")

    rows_finais = list(out_rows_map.values())
    _salvar_csv(QUALITY_CSV, rows_finais)

    print("\nFinalizado.")
    print(f"Novos OK nesta rodada: {novos_ok}")
    print(f"Total de OK no CSV: {len(rows_finais)}")
    print(f"Arquivo final: {QUALITY_CSV}")


if __name__ == "__main__":
    executar_pipeline()