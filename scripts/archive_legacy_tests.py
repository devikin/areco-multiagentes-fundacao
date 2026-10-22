"""Arquiva regressões históricas incompatíveis com o Agents SDK-only atual.

Uso:
  python scripts/archive_legacy_tests.py          # prévia: não modifica arquivos
  python scripts/archive_legacy_tests.py --apply  # move arquivos com SHA-256
  python scripts/archive_legacy_tests.py --restore # desfaz a migração

Não altera aplicativo, dados, .env ou testes modernos. Falha de modo explícito.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = ROOT / "tests"
ARCHIVE = ROOT / "docs" / "tests_historicos"
MANIFEST = ARCHIVE / "manifest-v035.json"

# Seleção revisada manualmente: tests históricos contra APIs retiradas ao
# migrar para Runner/SQLiteSession e resposta social gerada pela própria LLM.
# Não é uma lista de testes que 'falharam' em execução funcional: vários nem
# conseguem ser coletados pela versão atual.
LEGACY = (
    "test_orchestrator_policy_v0210.py",
    "test_scope_guard_v0212.py",
    "test_official_regression_v0213.py",
    "test_conversational_v0216.py",
    "test_social_fallback_v0217.py",
    "test_session_conversation_v0218.py",
    "test_browser_regression_v0219.py",
    "test_human_fallback_v0220.py",
    "test_ouvidoria_followup_v0220.py",
    "test_ui_version_v0221.py",
    "test_input_validation_v0222.py",
    "test_followup_year_v0223.py",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def archive(*, apply: bool) -> None:
    pending = [name for name in LEGACY if (ORIGIN / name).is_file()]
    already = [name for name in LEGACY if (ARCHIVE / name).is_file()]
    invalid = [name for name in LEGACY if (ORIGIN / name).exists() and not (ORIGIN / name).is_file()]
    if invalid:
        raise RuntimeError(f"Caminhos de origem inesperados: {invalid}")
    clashes = [name for name in pending if (ARCHIVE / name).exists()]
    if clashes:
        raise RuntimeError(f"Destino ocupado; nada foi movido: {clashes}")
    print(f"Arquivos legados ainda em tests/: {len(pending)}")
    print(f"Arquivos já arquivados: {len(already)}")
    for name in pending:
        print("  ", name)
    if not apply:
        print("Prévia apenas. Use --apply para mover; --restore para desfazer.")
        return
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    old_records = {}
    if MANIFEST.exists():
        old = json.loads(MANIFEST.read_text(encoding="utf-8"))
        old_records = {r["name"]: r for r in old.get("files", [])}
    records = dict(old_records)
    for name in pending:
        src, dst = ORIGIN / name, ARCHIVE / name
        before = sha256(src)
        shutil.move(str(src), str(dst))
        if sha256(dst) != before:
            raise RuntimeError(f"Hash diferente após mover {name}. Verifique manualmente.")
        records[name] = {"name": name, "sha256": before,
                         "original": f"tests/{name}",
                         "archive": f"docs/tests_historicos/{name}"}
    MANIFEST.write_text(json.dumps({
        "reason": "testes de contrato histórico substituído; sem descarte de evidências",
        "app_version": "0.2.35",
        "updated_utc": datetime.now(timezone.utc).isoformat(),
        "files": [records[n] for n in LEGACY if n in records],
    }, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"Arquivados {len(pending)} arquivo(s). Registro: {MANIFEST.relative_to(ROOT)}")
    print("O pytest não coleta mais esses módulos porque estão fora da pasta tests/.")


def restore() -> None:
    if not MANIFEST.exists():
        print("Nenhum manifest de migração encontrado. Nada foi alterado.")
        return
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    records = manifest.get("files", [])
    for item in records:
        name = item["name"]
        if name not in LEGACY:
            raise RuntimeError(f"Registro não autorizado: {name}")
        src, dst = ARCHIVE / name, ORIGIN / name
        if not src.exists():
            continue
        if dst.exists():
            raise RuntimeError(f"Já existe {dst}; restauração interrompida.")
        if sha256(src) != item["sha256"]:
            raise RuntimeError(f"Hash alterado para {name}; restauração interrompida.")
    count = 0
    for item in records:
        src, dst = ARCHIVE / item["name"], ORIGIN / item["name"]
        if src.exists():
            shutil.move(str(src), str(dst))
            count += 1
    print(f"Restaurados {count} arquivos para tests/. Manifest mantido para auditoria.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--apply", action="store_true", help="Executa o arquivamento seguro.")
    group.add_argument("--restore", action="store_true", help="Restaura os testes ao local original.")
    args = parser.parse_args()
    if args.restore:
        restore()
    else:
        archive(apply=args.apply)

if __name__ == "__main__":
    main()
