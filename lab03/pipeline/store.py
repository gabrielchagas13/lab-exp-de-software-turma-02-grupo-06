"""Gravação por repositório com retomada: reaproveita o JSON se já existir."""
import json
import os


def load_or_build(out_dir, repo, build):
    """Retorna `out_dir/<owner>__<repo>.json`; se não existe, chama `build()` e grava."""
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, repo.replace("/", "__") + ".json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    result = build()
    with open(path + ".tmp", "w", encoding="utf-8") as f:
        json.dump(result, f)
    os.replace(path + ".tmp", path)  # escrita atômica
    return result
