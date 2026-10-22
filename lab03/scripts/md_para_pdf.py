"""Converte o relatório em Markdown para PDF, replicando o modelo do professor.

Não há pandoc, LaTeX nem WeasyPrint no ambiente (o último depende de GTK, que
não está instalado), então o PDF é montado direto com `reportlab`, que é
pure-Python.

O layout segue o `Template_Relatorio_Laboratorio.pdf`:

- **Fonte Calibri** (lida de `C:/Windows/Fonts`), a mesma do modelo; se não for
  encontrada, cai para Helvetica e avisa.
- **Capa** com título azul centralizado, régua horizontal, subtítulo em itálico
  verde e a tabela de identificação com borda preta fina e rótulos em negrito
  na primeira coluna, sem preenchimento de fundo.
- **Títulos numerados** em azul; subtítulos de terceiro nível em verde.
- **Tabelas do corpo** com cabeçalho verde-escuro e texto branco em negrito.

Manter o Markdown como fonte única evita que duas versões do mesmo relatório
divirjam — o PDF é sempre regerado a partir dele.

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
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (HRFlowable, Image, ListFlowable, ListItem,
                                PageBreak, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

# Cores retiradas do modelo: azul dos títulos e verde das orientações/cabeçalhos.
AZUL = colors.HexColor("#1F4E79")
VERDE = colors.HexColor("#2E7D5B")
PRETO = colors.HexColor("#000000")
CINZA_TEXTO = colors.HexColor("#595959")

MARGEM = 2.2 * cm
LARGURA_UTIL = A4[0] - 2 * MARGEM

FONTES_WINDOWS = "C:/Windows/Fonts"
CALIBRI = {"normal": "calibri.ttf", "negrito": "calibrib.ttf",
           "italico": "calibrii.ttf", "negrito_italico": "calibriz.ttf"}


def registrar_fontes():
    """Registra Calibri; devolve (fonte_normal, fonte_negrito, fonte_italico)."""
    caminhos = {k: os.path.join(FONTES_WINDOWS, v) for k, v in CALIBRI.items()}
    if not all(os.path.isfile(c) for c in caminhos.values()):
        print("[aviso] Calibri nao encontrada; usando Helvetica.", file=sys.stderr)
        return "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"
    pdfmetrics.registerFont(TTFont("Calibri", caminhos["normal"]))
    pdfmetrics.registerFont(TTFont("Calibri-Bold", caminhos["negrito"]))
    pdfmetrics.registerFont(TTFont("Calibri-Italic", caminhos["italico"]))
    pdfmetrics.registerFont(TTFont("Calibri-BoldItalic", caminhos["negrito_italico"]))
    # registerFontFamily faz <b> e <i> dentro de Paragraph escolherem a variante certa
    pdfmetrics.registerFontFamily("Calibri", normal="Calibri", bold="Calibri-Bold",
                                  italic="Calibri-Italic", boldItalic="Calibri-BoldItalic")
    return "Calibri", "Calibri-Bold", "Calibri-Italic"


def estilos(normal, negrito, italico):
    return {
        "capa_titulo": ParagraphStyle("capa_titulo", fontName=normal, fontSize=26,
                                      textColor=AZUL, alignment=TA_CENTER,
                                      leading=30, spaceAfter=4),
        "capa_sub": ParagraphStyle("capa_sub", fontName=italico, fontSize=11,
                                   textColor=VERDE, alignment=TA_CENTER,
                                   leading=14, spaceBefore=8, spaceAfter=14),
        "h1": ParagraphStyle("h1", fontName=negrito, fontSize=14, textColor=AZUL,
                             leading=18, spaceBefore=16, spaceAfter=8),
        "h2": ParagraphStyle("h2", fontName=negrito, fontSize=12, textColor=AZUL,
                             leading=15, spaceBefore=13, spaceAfter=6),
        "h3": ParagraphStyle("h3", fontName=negrito, fontSize=10.5, textColor=VERDE,
                             leading=13, spaceBefore=10, spaceAfter=5),
        "corpo": ParagraphStyle("corpo", fontName=normal, fontSize=10.5, leading=14,
                                alignment=TA_JUSTIFY, spaceAfter=7),
        "celula": ParagraphStyle("celula", fontName=normal, fontSize=8.5, leading=11),
        "celula_neg": ParagraphStyle("celula_neg", fontName=negrito, fontSize=8.5,
                                     leading=11),
        "celula_cab": ParagraphStyle("celula_cab", fontName=negrito, fontSize=8.5,
                                     leading=11, textColor=colors.white),
        "legenda": ParagraphStyle("legenda", fontName=italico, fontSize=8.5, leading=11,
                                  alignment=TA_CENTER, textColor=CINZA_TEXTO,
                                  spaceAfter=10),
        "citacao": ParagraphStyle("citacao", fontName=italico, fontSize=9.5, leading=13,
                                  leftIndent=14, textColor=VERDE, spaceAfter=7),
    }


def inline(texto):
    t = html.escape(texto, quote=False)
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<link href="\2" color="#1F4E79">\1</link>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", t)
    t = re.sub(r"`([^`]+)`", r"<b>\1</b>", t)
    return t


def _celulas(linha):
    return [c.strip() for c in linha.strip().strip("|").split("|")]


def _larguras(n):
    if n == 1:
        return [LARGURA_UTIL]
    primeira = LARGURA_UTIL * (0.32 if n > 2 else 0.35)
    return [primeira] + [(LARGURA_UTIL - primeira) / (n - 1)] * (n - 1)


def tabela_capa(linhas, st):
    """Tabela de identificação: borda preta, rótulos em negrito, sem cabeçalho colorido."""
    dados = [[Paragraph(inline(c[0]), st["celula_neg"]),
              Paragraph(inline(c[1]) if len(c) > 1 else "", st["celula"])]
             for c in (_celulas(l) for l in linhas) if c and c[0]]
    t = Table(dados, colWidths=[LARGURA_UTIL * 0.34, LARGURA_UTIL * 0.66], hAlign="CENTER")
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.75, PRETO),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def tabela_corpo(linhas, st):
    """Tabela comum: cabeçalho verde com texto branco, grade preta fina."""
    cabecalho = _celulas(linhas[0])
    corpo = [_celulas(l) for l in linhas[2:]]
    n = len(cabecalho)
    corpo = [c + [""] * (n - len(c)) if len(c) < n else c[:n] for c in corpo]

    dados = [[Paragraph(inline(c), st["celula_cab"]) for c in cabecalho]]
    dados += [[Paragraph(inline(c), st["celula"]) for c in linha] for linha in corpo]

    t = Table(dados, colWidths=_larguras(n), repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), VERDE),
        ("GRID", (0, 0), (-1, -1), 0.5, PRETO),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def _imagem(caminho, base_dir):
    completo = os.path.normpath(os.path.join(base_dir, caminho))
    if not os.path.isfile(completo):
        return None
    from reportlab.lib.utils import ImageReader
    larg, alt = ImageReader(completo).getSize()
    escala = min(LARGURA_UTIL / larg, 1.0)
    return Image(completo, width=larg * escala, height=alt * escala)


def _bloco_tabela(linhas, i):
    """Se começa uma tabela em `i`, devolve (linhas_da_tabela, proximo_i)."""
    if not linhas[i].lstrip().startswith("|"):
        return None, i
    if i + 1 >= len(linhas):
        return None, i
    sep = linhas[i + 1].strip().replace("|", "").replace(" ", "")
    if not sep or set(sep) - {"-", ":"}:
        return None, i
    bloco, j = [linhas[i].rstrip()], i + 1
    while j < len(linhas) and linhas[j].strip().startswith("|"):
        bloco.append(linhas[j].rstrip())
        j += 1
    return bloco, j


def montar_capa(linhas, st, subtitulo):
    """Monta a capa a partir do bloco antes do primeiro separador `---`."""
    fluxo, titulo, tabela = [], None, None
    i = 0
    while i < len(linhas):
        bruta = linhas[i].rstrip()
        if bruta.startswith("# "):
            titulo = bruta[2:].strip()
            i += 1
            continue
        bloco, prox = _bloco_tabela(linhas, i)
        if bloco:
            tabela = bloco
            i = prox
            continue
        i += 1

    fluxo.append(Spacer(1, 2.2 * cm))
    fluxo.append(Paragraph(inline(titulo or "Relatório de Laboratório"), st["capa_titulo"]))
    fluxo.append(HRFlowable(width="88%", thickness=1.1, color=AZUL,
                            spaceBefore=2, spaceAfter=2, hAlign="CENTER"))
    fluxo.append(Paragraph(subtitulo, st["capa_sub"]))
    fluxo.append(Spacer(1, 0.6 * cm))
    if tabela:
        # A tabela da capa não tem linha de separação Markdown se for key-value
        # pura; trata as duas formas.
        corpo = tabela[2:] if len(tabela) > 1 and set(
            tabela[1].strip().replace("|", "").replace(" ", "")) <= {"-", ":"} else tabela
        fluxo.append(tabela_capa(corpo, st))
    fluxo.append(PageBreak())
    return fluxo


def converter(md_path, pdf_path, subtitulo):
    normal, negrito, italico = registrar_fontes()
    st = estilos(normal, negrito, italico)
    base_dir = os.path.dirname(os.path.abspath(md_path))
    with open(md_path, encoding="utf-8") as f:
        linhas = f.read().splitlines()

    # A capa é tudo que vem antes do primeiro separador horizontal.
    corte = next((k for k, l in enumerate(linhas) if l.strip() == "---"), 0)
    fluxo = montar_capa(linhas[:corte], st, subtitulo)

    i, bullets = corte + 1, []

    def descarregar():
        if bullets:
            fluxo.append(ListFlowable(
                [ListItem(Paragraph(inline(b), st["corpo"]), leftIndent=14)
                 for b in bullets],
                bulletType="bullet", start="\u25cf", leftIndent=16,
                bulletFontSize=6, bulletOffsetY=-1))
            bullets.clear()

    while i < len(linhas):
        bruta = linhas[i].rstrip()

        if not bruta.strip():
            descarregar()
            i += 1
            continue

        bloco, prox = _bloco_tabela(linhas, i)
        if bloco:
            descarregar()
            fluxo.append(tabela_corpo(bloco, st))
            fluxo.append(Spacer(1, 9))
            i = prox
            continue

        m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$", bruta.strip())
        if m:
            descarregar()
            img = _imagem(m.group(2), base_dir)
            if img is not None:
                fluxo.append(Spacer(1, 4))
                fluxo.append(img)
                fluxo.append(Spacer(1, 3))
            i += 1
            continue

        if bruta.startswith("#"):
            descarregar()
            nivel = len(bruta) - len(bruta.lstrip("#"))
            texto = bruta.lstrip("#").strip()
            fluxo.append(Paragraph(inline(texto), st[f"h{min(max(nivel - 1, 1), 3)}"]))
            i += 1
            continue

        if bruta.strip() in ("---", "***", "___"):
            descarregar()
            i += 1
            continue

        if bruta.lstrip().startswith("> "):
            descarregar()
            fluxo.append(Paragraph(inline(bruta.lstrip()[2:]), st["citacao"]))
            i += 1
            continue

        if re.match(r"^\s*[-*]\s+", bruta):
            bullets.append(re.sub(r"^\s*[-*]\s+", "", bruta))
            i += 1
            continue

        corpo_txt = bruta.strip()
        if corpo_txt.startswith("*") and corpo_txt.endswith("*") and \
                not corpo_txt.startswith("**"):
            descarregar()
            fluxo.append(Paragraph(inline(corpo_txt), st["legenda"]))
            i += 1
            continue

        descarregar()
        paragrafo, j = [corpo_txt], i + 1
        while j < len(linhas) and linhas[j].strip() and \
                not re.match(r"^\s*([-*#>|]|!\[)", linhas[j]) and \
                linhas[j].strip() != "---":
            paragrafo.append(linhas[j].strip())
            j += 1
        fluxo.append(Paragraph(inline(" ".join(paragrafo)), st["corpo"]))
        i = j

    descarregar()

    def rodape(canvas, doc):
        if doc.page == 1:
            return                      # a capa do modelo não tem rodapé
        canvas.saveState()
        canvas.setFont(normal, 8)
        canvas.setFillColor(CINZA_TEXTO)
        canvas.drawRightString(A4[0] - MARGEM, 1.2 * cm, str(doc.page))
        canvas.drawString(MARGEM, 1.2 * cm, subtitulo)
        canvas.restoreState()

    doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                            leftMargin=MARGEM, rightMargin=MARGEM,
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
    parser.add_argument("--subtitulo",
                        default="Laboratório de Experimentação de Software — "
                                "Lab03: Mineração de Métricas DORA")
    args = parser.parse_args(argv)
    caminho = converter(args.entrada, args.saida, args.subtitulo)
    print(f"PDF gerado: {caminho} ({os.path.getsize(caminho) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
