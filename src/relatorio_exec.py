"""
Gerador de Relatório Executivo (PDF) — tema azul, nível executivo.
Reutilizável pelos 3 projetos. Usa reportlab (Platypus).
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image,
                                Table, TableStyle, PageBreak, HRFlowable, ListFlowable, ListItem)
from reportlab.lib.utils import ImageReader

ESCURO = colors.HexColor("#1f4e79")
MEDIO = colors.HexColor("#2e6da4")
CLARO = colors.HexColor("#5b9bd5")
SUAVE = colors.HexColor("#eef3f9")
CINZA = colors.HexColor("#5b6b7d")
ALERTA = colors.HexColor("#c0392b")

def _styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle("Titulo", parent=s["Title"], textColor=ESCURO, fontSize=24,
                         leading=28, spaceAfter=2, alignment=TA_LEFT))
    s.add(ParagraphStyle("Sub", parent=s["Normal"], textColor=MEDIO, fontSize=13,
                         leading=16, spaceAfter=2))
    s.add(ParagraphStyle("Meta", parent=s["Normal"], textColor=CINZA, fontSize=9, spaceAfter=6))
    s.add(ParagraphStyle("H2", parent=s["Heading2"], textColor=ESCURO, fontSize=14,
                         leading=18, spaceBefore=14, spaceAfter=6))
    s.add(ParagraphStyle("Corpo", parent=s["Normal"], fontSize=10.5, leading=15.5,
                         alignment=TA_JUSTIFY, textColor=colors.HexColor("#2b2b2b"), spaceAfter=6))
    s.add(ParagraphStyle("Cap", parent=s["Normal"], fontSize=8, textColor=CINZA,
                         alignment=TA_CENTER, spaceAfter=10))
    s.add(ParagraphStyle("KpiNum", parent=s["Normal"], fontSize=16, leading=18,
                         textColor=ESCURO, alignment=TA_CENTER, fontName="Helvetica-Bold"))
    s.add(ParagraphStyle("KpiLab", parent=s["Normal"], fontSize=8, leading=10,
                         textColor=CINZA, alignment=TA_CENTER))
    s.add(ParagraphStyle("BulletItem", parent=s["Normal"], fontSize=10.5, leading=15, textColor=colors.HexColor("#2b2b2b")))
    return s

def _img(path, largura_cm=16.5):
    ir = ImageReader(path); iw, ih = ir.getSize()
    w = largura_cm * cm; h = w * ih / iw
    return Image(path, width=w, height=h)

def _kpi_table(kpis):
    cells = [[Paragraph(v, _styles()["KpiNum"]) for v, _ in kpis],
             [Paragraph(l, _styles()["KpiLab"]) for _, l in kpis]]
    t = Table(cells, colWidths=[ (16.5/len(kpis))*cm ]*len(kpis))
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), SUAVE),
        ("BOX", (0,0), (-1,-1), 0.5, CLARO),
        ("INNERGRID", (0,0), (-1,-1), 0.5, colors.white),
        ("TOPPADDING",(0,0),(-1,0),10),("BOTTOMPADDING",(0,1),(-1,1),10),
        ("TOPPADDING",(0,1),(-1,1),0),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    return t

def construir(config, saida):
    s = _styles()
    def page(canvas, doc):
        canvas.saveState()
        # faixa superior
        canvas.setFillColor(ESCURO); canvas.rect(0, A4[1]-1.0*cm, A4[0], 1.0*cm, fill=1, stroke=0)
        canvas.setFillColor(CLARO); canvas.rect(0, A4[1]-1.12*cm, A4[0], 0.12*cm, fill=1, stroke=0)
        # rodapé
        canvas.setFillColor(CINZA); canvas.setFont("Helvetica", 7.5)
        canvas.drawString(2*cm, 1.0*cm, config.get("fonte",""))
        canvas.drawRightString(A4[0]-2*cm, 1.0*cm, f"Pág. {doc.page}")
        canvas.setStrokeColor(colors.HexColor("#d9e2ec")); canvas.line(2*cm,1.3*cm,A4[0]-2*cm,1.3*cm)
        canvas.restoreState()

    doc = SimpleDocTemplate(saida, pagesize=A4, topMargin=1.7*cm, bottomMargin=1.8*cm,
                            leftMargin=2*cm, rightMargin=2*cm, title=config["titulo"],
                            author="Ana Paula Galdino")
    story = []
    story.append(Paragraph(config.get("eyebrow", "RELATÓRIO EXECUTIVO"), s["Sub"]))
    story.append(Paragraph(config["titulo"], s["Titulo"]))
    story.append(Paragraph(config["subtitulo"], s["Sub"]))
    story.append(Paragraph(config["meta"], s["Meta"]))
    story.append(HRFlowable(width="100%", thickness=1.4, color=ESCURO, spaceAfter=10))

    story.append(Paragraph("Sumário Executivo", s["H2"]))
    for p in config["sumario"]:
        story.append(Paragraph(p, s["Corpo"]))
    story.append(Spacer(1, 6))
    story.append(_kpi_table(config["kpis"]))
    story.append(Spacer(1, 6))

    for sec in config["secoes"]:
        blocos = []
        blocos.append(Paragraph(sec["titulo"], s["H2"]))
        for p in sec.get("texto", []):
            blocos.append(Paragraph(p, s["Corpo"]))
        for img, cap in sec.get("imagens", []):
            blocos.append(_img(img))
            if cap: blocos.append(Paragraph(cap, s["Cap"]))
        story += blocos

    story.append(Paragraph(config["conclusao_titulo"], s["H2"]))
    items = [ListItem(Paragraph(b, s["BulletItem"]), value="•") for b in config["conclusoes"]]
    story.append(ListFlowable(items, bulletType="bullet", bulletColor=ESCURO, leftIndent=12))

    doc.build(story, onFirstPage=page, onLaterPages=page)
    print("PDF gerado:", saida)
