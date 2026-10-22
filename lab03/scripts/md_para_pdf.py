"""Converte o relatório em Markdown para PDF, no layout do modelo do professor.

Não há pandoc, LaTeX nem WeasyPrint disponíveis no ambiente (o último depende
de GTK, que não está instalado no Windows), então o PDF é montado direto com
`reportlab`, que é pure-Python. O renderizador cobre o subconjunto de Markdown
usado no relatório: títulos de 1 a 4 níveis, parágrafos, tabelas com cabeçalho,
listas, citações, imagens, regra horizontal e os inlines `**negrito**`,
`*itálico*` e `` `código` ``.

Manter o Markdown como fonte única evita o problema clássico de duas versões do
mesmo relatório divergirem — o PDF é sempre regerado a partir dele.

Uso:
    python -m scripts.md_para_pdf docs/relatorio_lab03.md docs/relatorio_lab03.pdf
"""
import argparse
import html
import os
import re
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (HRFlowable, Image, ListFlowable, ListItem,
                                PageBreak, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

AZUL = colors.HexColor("#1F4E79")
VERDE = colors.HexColor("#2E7D5B")
CINZA_LINHA = colors.HexColor("#999999")
CINZA_FUNDO = colors.HexColor("#F2F2F2")
LARGURA_UTIL = A4[0] - 4 * cm


def estilos():
    base = getSampleStyleSheet()
    s = {
        "titulo": ParagraphStyle("titulo", parent=base["Title"], fontSize=20,
                                 textColor=AZUL, spaceAfter=14),
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontSize=15,
                             textColor=AZUL, spaceBefore=16, spaceAfter=8),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontSize=12.5,
                             textColor=AZUL, spaceBefore=12, spaceAfter=6),
        "h3": ParagraphStyle("h3", parent=base["Heading3"], fontSize=11,
                             textColor=VERDE, spaceBefore=10, spaceAfter=5),
        "corpo": ParagraphStyle("corpo", parent=base["BodyText"], fontSize=9.5,
                                leading=13.5, alignment=TA_JUSTIFY, spaceAfter=6),
        "celula": ParagraphStyle("celula", parent=base["BodyText"], fontSize=8,
                                 leading=10.5, spaceAfter=0),
        "celula_cab": ParagraphStyle("celula_cab", parent=base["BodyText"], fontSize=8,
                                     leading=10.5, spaceAfter=0,
                                     textColor=colors.white, fontName="Helvetica-Bold"),
        "legenda": ParagraphStyle("legenda", parent=base["BodyText"], fontSize=8,
                                  leading=11, alignment=TA_CENTER,
                                  textColor=colors.HexColor("#555555"), spaceAfter=10),
        "citacao": ParagraphStyle("citacao", parent=base["BodyText"], fontSize=9,
                                  leading=12.5, leftIndent=12, textColor=VERDE,
                                  spaceAfter=6),
    }
    return s


def inline(texto):
    """Converte os inlines de Markdown para as tags que o reportlab entende."""
    t = html.escape(texto, quote=False)
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", t)                      # imagem tratada à parte
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<link href="\2" color="#1F4E79">\1</link>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", t)
    t = re.sub(r"`([^`]+)`", r'<font face="Courier" size="8.5">\1</font>', t)
    return t


def _celulas(linha):
    return [c.strip() for c in linha.strip().strip("|").split("|")]


def _tabela(linhas, st):
    """Monta uma Table a partir das linhas Markdown (cabeçalho + separador + corpo)."""
    cabecalho = _celulas(linhas[0])
    corpo = [_celulas(l) for l in linhas[2:]]
    n = len(cabecalho)
    corpo = [c + [""] * (n - len(c)) if len(c) < n else c[:n] for c in corpo]

    dados = [[Paragraph(inline(c), st["celula_cab"]) for c in cabecalho]]
    dados += [[Paragraph(inline(c), st["celula"]) for c in linha] for linha in corpo]

    # Primeira coluna um pouco mais larga: nas tabelas do relatório ela costuma
    # ser o rótulo (métrica, decisão, etapa) e o resto é texto curto.
    if n == 1:
        larguras = [LARGURA_UTIL]
    else:
        primeira = LARGURA_UTIL * (0.30 if n > 2 else 0.38)
        larguras = [primeira] + [(LARGURA_UTIL - primeira) / (n - 1)] * (n - 1)

    t = Table(dados, colWidths=larguras, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CINZA_FUNDO]),
        ("GRID", (0, 0), (-1, -1), 0.4, CINZA_LINHA),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def _imagem(caminho, base_dir):
    """Imagem reduzida à largura útil, preservando a proporção."""
    completo = os.path.normpath(os.path.join(base_dir, caminho))
    if not os.path.isfile(completo):
        return None
    from reportlab.lib.utils import ImageReader
    larg, alt = ImageReader(completo).getSize()
    escala = min(LARGURA_UTIL / larg, 1.0)
    return Image(completo, width=larg * escala, height=alt * escala)


def converter(md_path, pdf_path):
    st = estilos()
    base_dir = os.path.dirname(os.path.abspath(md_path))
    with open(md_path, encoding="utf-8") as f:
        linhas = f.read().splitlines()

    fluxo, i, bullets = [], 0, []

    def descarregar_bullets():
        if bullets:
            fluxo.append(ListFlowable(
                [ListItem(Paragraph(inline(b), st["corpo"]), leftIndent=12) for b in bullets],
                bulletType="bullet", start="•", leftIndent=14))
            bullets.clear()

    while i < len(linhas):
        linha = linhas[i]
        bruta = linha.rstrip()

        if not bruta.strip():
            descarregar_bullets()
            i += 1
            continue

        # tabela: cabeçalho seguido de linha de separação
        if bruta.lstrip().startswith("|") and i + 1 < len(linhas) and \
                set(linhas[i + 1].strip().replace("|", "").replace(" ", "")) <= {"-", ":"}:
            descarregar_bullets()
            bloco = [bruta]
            j = i + 1
            while j < len(linhas) and linhas[j].strip().startswith("|"):
                bloco.append(linhas[j].rstrip())
                j += 1
            fluxo.append(_tabela(bloco, st))
            fluxo.append(Spacer(1, 8))
            i = j
            continue

        # imagem isolada
        m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$", bruta.strip())
        if m:
            descarregar_bullets()
            img = _imagem(m.group(2), base_dir)
            if img is not None:
                fluxo.append(Spacer(1, 4))
                fluxo.append(img)
                fluxo.append(Spacer(1, 3))
            i += 1
            continue

        if bruta.startswith("#"):
            descarregar_bullets()
            nivel = len(bruta) - len(bruta.lstrip("#"))
            texto = bruta.lstrip("#").strip()
            if nivel == 1:
                fluxo.append(Paragraph(inline(texto), st["titulo"]))
            else:
                fluxo.append(Paragraph(inline(texto), st[f"h{min(nivel - 1, 3)}"]))
            i += 1
            continue

        if bruta.strip() in ("---", "***", "___"):
            descarregar_bullets()
            fluxo.append(Spacer(1, 4))
            fluxo.append(HRFlowable(width="100%", thickness=0.6, color=CINZA_LINHA))
            fluxo.append(Spacer(1, 6))
            i += 1
            continue

        if bruta.lstrip().startswith("> "):
            descarregar_bullets()
            fluxo.append(Paragraph(inline(bruta.lstrip()[2:]), st["citacao"]))
            i += 1
            continue

        if re.match(r"^\s*[-*]\s+", bruta):
            bullets.append(re.sub(r"^\s*[-*]\s+", "", bruta))
            i += 1
            continue

        # legenda de figura: parágrafo inteiro em itálico, logo após uma imagem
        if bruta.strip().startswith("*") and bruta.strip().endswith("*") and \
                not bruta.strip().startswith("**"):
            descarregar_bullets()
            fluxo.append(Paragraph(inline(bruta.strip()), st["legenda"]))
            i += 1
            continue

        descarregar_bullets()
        paragrafo = [bruta.strip()]
        j = i + 1
        while j < len(linhas) and linhas[j].strip() and not re.match(
                r"^\s*([-*#>|]|!\[)", linhas[j]) and linhas[j].strip() not in ("---",):
            paragrafo.append(linhas[j].strip())
            j += 1
        fluxo.append(Paragraph(inline(" ".join(paragrafo)), st["corpo"]))
        i = j

    descarregar_bullets()

    def rodape(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.HexColor("#777777"))
        canvas.drawRightString(A4[0] - 2 * cm, 1.3 * cm, f"{doc.page}")
        canvas.drawString(2 * cm, 1.3 * cm,
                          "Lab03 — Mineração de Métricas DORA · Grupo 06")
        canvas.restoreState()

    doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                            leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm,
                            title="Relatório de Laboratório — Lab03",
                            author="Gabriel Chagas, Guilherme Lana, Marcus Vinicius")
    doc.build(fluxo, onFirstPage=rodape, onLaterPages=rodape)
    return pdf_path


def main(argv=None):
    parser = argparse.ArgumentParser(prog="scripts.md_para_pdf", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("entrada", nargs="?", default=os.path.join("docs", "relatorio_lab03.md"))
    parser.add_argument("saida", nargs="?", default=os.path.join("docs", "relatorio_lab03.pdf"))
    args = parser.parse_args(argv)
    caminho = converter(args.entrada, args.saida)
    tamanho = os.path.getsize(caminho) / 1024
    print(f"PDF gerado: {caminho} ({tamanho:.0f} KB)")


if __name__ == "__main__":
    main()
