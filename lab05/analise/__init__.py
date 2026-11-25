"""Análise de dados do Lab05.

Ao importar o pacote (sempre que se roda ``python -m analise.<script>``),
garantimos que stdout/stderr usem UTF-8. Sem isso, o console padrão do
Windows (cp1252) derruba os scripts com UnicodeEncodeError ao imprimir
caracteres como ``✓``, ``✗`` ou ``⚠``.
"""
import sys as _sys


def _forcar_utf8(stream) -> None:
    try:
        enc = (getattr(stream, "encoding", "") or "").lower()
        if enc not in ("utf-8", "utf8") and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    except Exception:
        pass


_forcar_utf8(_sys.stdout)
_forcar_utf8(_sys.stderr)
