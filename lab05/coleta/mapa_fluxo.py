"""Mapeia as telas do fluxo "perda de documentos e objetos" da Delegacia Virtual.

O fluxo é um wizard renderizado no servidor. As três primeiras telas têm URL
própria e são alcançáveis por GET; da quarta em diante o avanço depende de um
POST com dados pessoais e captcha, que **não fazemos** (ver `docs/
fluxo_perda_documento.md` e a seção de ética do enunciado).

Este módulo percorre apenas as telas alcançáveis por GET, uma requisição por
tela com no mínimo 1 s de intervalo, e grava uma linha por tela em
`data/fluxo/telas.csv` com o que importa para as RQ1 e RQ2: título, cabeçalho,
quantidade de campos de formulário, presença de captcha e de relógio de sessão,
peso e tempo de resposta.

A trava contra envio é estrutural: a sessão usada aqui recusa qualquer método
que não seja GET ou HEAD, então nenhuma alteração futura deste arquivo consegue
submeter um formulário sem que o teste automatizado quebre.

    python -m coleta.mapa_fluxo --config config.json
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import requests

CAMPOS = [
    "timestamp_utc", "id", "etapa", "nome", "url", "status_http", "ok",
    "tempo_s", "bytes", "titulo", "cabecalho", "campos_formulario",
    "tem_captcha", "tem_relogio_sessao", "avanca_para", "metodo_avanco", "erro",
]

# Pistas no HTML. Mantidas aqui, e não espalhadas pelo código, porque é o
# primeiro lugar a ajustar se a Delegacia Virtual mudar o layout.
MARCA_CAPTCHA = re.compile(r"captch", re.I)
MARCA_RELOGIO = re.compile(r"content-relogio|renovaSessao", re.I)
RE_TITULO = re.compile(r"<title[^>]*>(.*?)</title>", re.S | re.I)
# Em ordem de prioridade: o <h2> é o que nomeia a tela nas três páginas do
# fluxo. O <legend> só entra como reserva porque, na tela inicial, ele rotula
# um banner de campanha e não a página.
RE_CABECALHOS = (
    re.compile(r"<h2[^>]*>(.*?)</h2>", re.S | re.I),
    re.compile(r"<legend[^>]*>(.*?)</legend>", re.S | re.I),
    re.compile(r"<h1[^>]*>(.*?)</h1>", re.S | re.I),
)
RE_CAMPO = re.compile(r'<(?:input|select|textarea)[^>]*name="([^"]+)"', re.I)
RE_FORM = re.compile(r'<form[^>]*action="([^"]*)"[^>]*>', re.I)
RE_LINK = re.compile(r'<a[^>]+href="([^"#]+)"[^>]*>(.*?)</a>', re.S | re.I)
RE_AVANCO = re.compile(r"continuar|avan|pr[oó]xim|estou ciente", re.I)

# Campos que não são do formulário da tela: diálogo de sessão e controles.
NAO_SAO_CAMPOS = {"radioInformaFimDaSessao", "botaoFechaDialogo"}


class SessaoSomenteLeitura(requests.Session):
    """Sessão que só deixa passar GET e HEAD.

    O estudo mede o serviço de fora, como um cidadão faria ao navegar. Enviar
    um boletim falso é crime (CP art. 340) e preencher formulário de terceiros
    automaticamente está fora do combinado com o professor. Em vez de confiar
    na disciplina de quem edita o arquivo, a proibição fica no código.
    """

    PERMITIDOS = {"GET", "HEAD"}

    def request(self, method, url, *args, **kwargs):  # noqa: D102
        if method.upper() not in self.PERMITIDOS:
            raise PermissionError(
                f"{method} bloqueado: o mapeamento do fluxo é somente leitura "
                "(nenhum formulário é enviado)."
            )
        return super().request(method, url, *args, **kwargs)


def _texto(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


def titulo(html: str) -> str:
    m = RE_TITULO.search(html)
    return _texto(m.group(1))[:120] if m else ""


def cabecalho(html: str) -> str:
    """O cabeçalho visível da tela.

    O primeiro <h2> é o que identifica a tela nas três páginas do fluxo; o
    <legend> serve de reserva, mas na tela inicial ele rotula um banner e não
    a página, por isso não vem primeiro.
    """
    for regex in RE_CABECALHOS:
        for m in regex.finditer(html):
            t = _texto(m.group(1))
            if t:
                return t[:120]
    return ""


def campos_formulario(html: str) -> list[str]:
    vistos, saida = set(), []
    for nome in RE_CAMPO.findall(html):
        if nome in NAO_SAO_CAMPOS or nome in vistos:
            continue
        vistos.add(nome)
        saida.append(nome)
    return saida


def avanco(html: str, url_proxima: str = "") -> tuple[str, str]:
    """Para onde a tela leva, e por qual método.

    A verificação que interessa ao mapeamento é esta: a próxima tela do fluxo
    aparece como link nesta aqui? Se aparece, a cadeia se sustenta por GET e o
    cidadão (e o Lighthouse) chega lá sem enviar nada. Se não aparece, o avanço
    é o `action` de um formulário — ou seja, POST — e o mapeamento automático
    termina nesta tela.
    """
    if url_proxima:
        caminho = urlsplit(url_proxima).path
        if caminho and caminho in html:
            return url_proxima, "GET"
    for url, texto in RE_LINK.findall(html):
        if RE_AVANCO.search(_texto(texto)) and "static" not in url:
            return url, "GET"
    m = RE_FORM.search(html)
    return (m.group(1), "POST") if m else ("", "")


def descrever(html: str, url_proxima: str = "") -> dict:
    campos = campos_formulario(html)
    destino, metodo = avanco(html, url_proxima)
    return {
        "titulo": titulo(html),
        "cabecalho": cabecalho(html),
        "campos_formulario": len(campos),
        "tem_captcha": int(bool(MARCA_CAPTCHA.search(html))),
        "tem_relogio_sessao": int(bool(MARCA_RELOGIO.search(html))),
        "avanca_para": destino,
        "metodo_avanco": metodo,
    }


def mapear(telas: list[dict], user_agent: str, intervalo: float = 1.0,
           sessao: requests.Session | None = None) -> list[dict]:
    s = sessao or SessaoSomenteLeitura()
    s.headers["User-Agent"] = user_agent
    mapeaveis = [t for t in telas if t.get("mapeavel", True)]
    linhas = []
    for i, tela in enumerate(mapeaveis):
        proxima = mapeaveis[i + 1]["url"] if i + 1 < len(mapeaveis) else ""
        if i:
            time.sleep(max(1.0, intervalo))
        linha = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "id": tela["id"], "etapa": tela["etapa"], "nome": tela["nome"],
            "url": tela["url"], "erro": "",
        }
        inicio = time.perf_counter()
        try:
            r = s.get(tela["url"], timeout=30)
            linha.update({
                "status_http": r.status_code,
                "ok": int(200 <= r.status_code < 400),
                "tempo_s": round(time.perf_counter() - inicio, 3),
                "bytes": len(r.content),
                **descrever(r.text, proxima),
            })
        except Exception as e:  # rede fora do ar, timeout, bloqueio
            linha.update({"status_http": "", "ok": 0,
                          "tempo_s": round(time.perf_counter() - inicio, 3),
                          "bytes": 0, "erro": type(e).__name__})
        linhas.append(linha)
    return linhas


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="config.json")
    ap.add_argument("--saida", default="data/fluxo/telas.csv")
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    fluxo = cfg["fluxo_perda_documento"]
    linhas = mapear(fluxo["telas"], cfg["user_agent"],
                    float(cfg["intervalo_min_requisicoes_s"]))

    saida = Path(args.saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    with saida.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        for linha in linhas:
            w.writerow({c: linha.get(c, "") for c in CAMPOS})

    for linha in linhas:
        print(f"{linha['etapa']} {linha['nome'][:34]:<34} "
              f"{linha['status_http']!s:>4} {linha.get('campos_formulario', ''):>3} campos "
              f"{'captcha' if linha.get('tem_captcha') else '       '} "
              f"-> {linha.get('metodo_avanco', '')}")
    nao = [t for t in fluxo["telas"] if not t.get("mapeavel", True)]
    if nao:
        print(f"\n{len(nao)} tela(s) não mapeáveis por GET (exigem POST com dados "
              f"pessoais e captcha): ver docs/fluxo_perda_documento.md")
    print(f"\nGravado em {saida}")


if __name__ == "__main__":
    main()
