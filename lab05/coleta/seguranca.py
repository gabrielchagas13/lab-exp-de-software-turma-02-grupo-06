"""Coleta passiva de segurança (RQ3): cabeçalhos HTTP, TLS e bibliotecas JS.

Só faz GET nas páginas públicas do config e nos scripts que elas carregam,
com >= 1 s entre requisições. Não testa vulnerabilidades, não envia payloads
nem formulários: apenas lê o que qualquer navegador recebe.

    python -m coleta.seguranca --config config.json

Saídas (sobrescritas a cada execução, com timestamp em cada linha):
    data/seguranca/cabecalhos.csv   página × cabeçalho recomendado (presente/valor)
    data/seguranca/tls.csv          host, versões TLS aceitas, emissor e validade do certificado
    data/seguranca/bibliotecas.csv  biblioteca, versão detectada, CVEs conhecidas
"""
import argparse
import csv
import json
import re
import socket
import ssl
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests

# Assinaturas de banner (comentário de licença no topo do arquivo minificado).
ASSINATURAS = {
    "jquery": re.compile(r"jQuery (?:JavaScript Library )?v(\d+\.\d+\.\d+)"),
    "jquery-ui": re.compile(r"jQuery UI - v(\d+\.\d+\.\d+)"),
    "bootstrap": re.compile(r"Bootstrap v(\d+\.\d+\.\d+)"),
    "moment": re.compile(r"(?:moment\.js|//! version) *:? *(\d+\.\d+\.\d+)"),
    "jquery-validation": re.compile(r"jQuery Validation Plugin v(\d+\.\d+\.\d+)"),
    "jquery-mask": re.compile(r"jquery\.mask\.js.*?@version:? *v?(\d+\.\d+\.\d+)", re.S),
    "popper": re.compile(r"@popperjs/core v(\d+\.\d+\.\d+)|Popper\.js v?(\d+\.\d+\.\d+)"),
    "font-awesome": re.compile(r"Font Awesome (?:Free )?(\d+\.\d+\.\d+)"),
}

# CVEs públicas relevantes: (biblioteca, corrigida_em, cve). Vulnerável se versão < corrigida_em.
CVES = [
    ("jquery", "1.9.0", "CVE-2012-6708"),
    ("jquery", "3.0.0", "CVE-2015-9251"),
    ("jquery", "3.4.0", "CVE-2019-11358"),
    ("jquery", "3.5.0", "CVE-2020-11022"),
    ("jquery", "3.5.0", "CVE-2020-11023"),
    ("jquery-ui", "1.13.0", "CVE-2021-41182"),
    ("jquery-ui", "1.13.0", "CVE-2021-41183"),
    ("jquery-ui", "1.13.0", "CVE-2021-41184"),
    ("jquery-ui", "1.13.2", "CVE-2022-31160"),
    ("bootstrap", "3.4.0", "CVE-2018-14041"),
    ("bootstrap", "3.4.1", "CVE-2019-8331"),
    ("moment", "2.29.2", "CVE-2022-24785"),
    ("moment", "2.29.4", "CVE-2022-31129"),
    ("jquery-validation", "1.19.3", "CVE-2021-21252"),
    ("jquery-validation", "1.19.5", "CVE-2022-43320"),
]
# Bootstrap 4.x tem correção própria para CVE-2019-8331 (4.3.1); tratada em cves_de().

CAMPOS_CAB = ["timestamp_utc", "pagina", "host", "cabecalho", "presente", "valor"]
CAMPOS_TLS = ["timestamp_utc", "host", "tls1_0", "tls1_1", "tls1_2", "tls1_3",
              "emissor", "valido_ate", "dias_para_expirar", "erro"]
CAMPOS_LIB = ["timestamp_utc", "pagina", "script", "biblioteca", "versao", "cves", "n_cves"]


def versao_tupla(v: str) -> tuple:
    return tuple(int(x) for x in re.findall(r"\d+", v)[:3])


def cves_de(lib: str, versao: str) -> list:
    v = versao_tupla(versao)
    out = []
    for nome, corrigida, cve in CVES:
        if nome != lib:
            continue
        if lib == "bootstrap" and cve == "CVE-2019-8331" and v[0] == 4:
            corrigida = "4.3.1"
        if lib == "bootstrap" and cve == "CVE-2018-14041" and v[0] >= 4:
            corrigida = "4.1.2"
        if v < versao_tupla(corrigida):
            out.append(cve)
    return out


def detectar_bibliotecas(js: str) -> list:
    """Procura banners de versão nos primeiros 5 KB (e em todo o arquivo, para bundles)."""
    achados = []
    for lib, rx in ASSINATURAS.items():
        for m in rx.finditer(js):
            versao = next(g for g in m.groups() if g)
            if (lib, versao) not in achados:
                achados.append((lib, versao))
    # "jquery-ui" também casa como "jquery"? não: o regex do jQuery exige "jQuery v" ou "Library v"
    return achados


def scripts_da_pagina(html: str, base: str) -> list:
    srcs = re.findall(r"<script[^>]+src=[\"']([^\"']+)[\"']", html, re.I)
    # ignora scripts em comentários condicionais do IE (<!--[if lt IE 9]>)
    ie = set(re.findall(r"<!--\[if[^\]]*\]>.*?<!\[endif\]-->", html, re.S | re.I))
    ie_srcs = {s for bloco in ie for s in re.findall(r"src=[\"']([^\"']+)", bloco)}
    return [urljoin(base, s) for s in srcs if s not in ie_srcs]


def testar_tls(host: str, timeout: float = 10.0) -> dict:
    warnings.filterwarnings("ignore", category=DeprecationWarning)  # TLS 1.0/1.1 são testados de propósito
    res = {}
    for nome, versao in [("tls1_0", ssl.TLSVersion.TLSv1), ("tls1_1", ssl.TLSVersion.TLSv1_1),
                         ("tls1_2", ssl.TLSVersion.TLSv1_2), ("tls1_3", ssl.TLSVersion.TLSv1_3)]:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        try:
            ctx.set_ciphers("ALL:@SECLEVEL=0")
            ctx.minimum_version = versao
            ctx.maximum_version = versao
        except (ValueError, ssl.SSLError):
            res[nome] = "nao_testavel"
            continue
        try:
            with socket.create_connection((host, 443), timeout=timeout) as s, \
                    ctx.wrap_socket(s, server_hostname=host):
                res[nome] = 1
        except (ssl.SSLError, OSError):
            res[nome] = 0
        time.sleep(1)
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=timeout) as s, \
                ctx.wrap_socket(s, server_hostname=host) as ss:
            cert = ss.getpeercert()
        fim = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
        emissor = dict(x[0] for x in cert["issuer"]).get("organizationName", "")
        res.update(emissor=emissor, valido_ate=fim.date().isoformat(),
                   dias_para_expirar=(fim - datetime.now(timezone.utc)).days, erro="")
    except (ssl.SSLError, OSError) as e:
        res.update(emissor="", valido_ate="", dias_para_expirar="", erro=type(e).__name__)
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.json")
    ap.add_argument("--saida", default="data/seguranca")
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    pausa = max(1.0, float(cfg["intervalo_min_requisicoes_s"]))
    ua = {"User-Agent": cfg["user_agent"]}
    cabecalhos = cfg["seguranca"]["cabecalhos"]
    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")

    linhas_cab, linhas_lib, hosts, vistos = [], [], [], {}
    for nome, url in cfg["paginas"].items():
        r = requests.get(url, headers=ua, timeout=30)
        time.sleep(pausa)
        host = urlparse(r.url).hostname
        if host not in hosts:
            hosts.append(host)
        for c in cabecalhos:
            linhas_cab.append({"timestamp_utc": ts, "pagina": nome, "host": host, "cabecalho": c,
                               "presente": int(c in r.headers), "valor": r.headers.get(c, "")[:200]})
        for src in scripts_da_pagina(r.text, r.url):
            if src not in vistos:
                try:
                    vistos[src] = detectar_bibliotecas(requests.get(src, headers=ua, timeout=30).text)
                except requests.RequestException:
                    vistos[src] = []
                time.sleep(pausa)
            for lib, versao in vistos[src]:
                cves = cves_de(lib, versao)
                linhas_lib.append({"timestamp_utc": ts, "pagina": nome, "script": src, "biblioteca": lib,
                                   "versao": versao, "cves": "|".join(cves), "n_cves": len(cves)})
        print(f"{nome:<24} faltam: {[c for c in cabecalhos if c not in r.headers]}")

    linhas_tls = [{"timestamp_utc": ts, "host": h, **testar_tls(h)} for h in hosts]

    for arq, campos, linhas in [("cabecalhos.csv", CAMPOS_CAB, linhas_cab),
                                ("tls.csv", CAMPOS_TLS, linhas_tls),
                                ("bibliotecas.csv", CAMPOS_LIB, linhas_lib)]:
        with (saida / arq).open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=campos)
            w.writeheader()
            w.writerows(linhas)
    for l in linhas_tls:
        print(l)
    for l in {(l["biblioteca"], l["versao"], l["cves"]) for l in linhas_lib}:
        print(l)


if __name__ == "__main__":
    main()
