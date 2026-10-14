# -*- coding: utf-8 -*-
"""
Génère le rapport PDF professionnel de couverture médiatique (MEDIA MONITORING AGENT V1.1).

Usage :
    python scripts/generer_rapport_pdf.py --cp CP-20261010-001 \
        --titre "..." --emetteur "..." --date-communique 2026-09-15 \
        --periode "15/09/2026 - 10/10/2026"

Lit reprises.csv (données réelles uniquement, est_test=non), sépare les catégories
confirmee / probable / non_verifiable et produit un PDF avec charte graphique
configurable (config/charte.json). Aucune donnée fictive, aucun envoi automatique.
"""
import argparse
import csv
import json
import pathlib
from collections import Counter
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak)
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

BASE = pathlib.Path(__file__).resolve().parent.parent


def esc(s):
    return escape(str(s))


def hex2rgb(h):
    h = str(h).lstrip("#")
    try:
        return colors.HexColor("#" + h)
    except Exception:
        return colors.HexColor("#333333")


def setup_fonts():
    """Tente Arial (Windows) puis DejaVu (Linux), enregistrés sous les noms Arial*. Sinon Helvetica."""
    wf = pathlib.Path("C:/Windows/Fonts")
    try:
        if (wf / "arial.ttf").exists():
            pdfmetrics.registerFont(TTFont("Arial", str(wf / "arial.ttf")))
            pdfmetrics.registerFont(TTFont("Arial-Bold", str(wf / "arialbd.ttf")))
            pdfmetrics.registerFont(TTFont("Arial-Italic", str(wf / "ariali.ttf")))
            pdfmetrics.registerFontFamily(
                "Arial", normal="Arial", bold="Arial-Bold",
                italic="Arial-Italic", boldItalic="Arial-Bold")
            return "Arial"
    except Exception:
        pass
    for d in ("/usr/share/fonts/truetype/dejavu/", "/usr/share/fonts/dejavu/"):
        try:
            n = d + "DejaVuSans.ttf"
            if pathlib.Path(n).exists():
                b = d + "DejaVuSans-Bold.ttf"
                pdfmetrics.registerFont(TTFont("Arial", n))
                pdfmetrics.registerFont(TTFont("Arial-Bold", b if pathlib.Path(b).exists() else n))
                pdfmetrics.registerFont(TTFont("Arial-Italic", n))
                pdfmetrics.registerFontFamily(
                    "Arial", normal="Arial", bold="Arial-Bold",
                    italic="Arial-Italic", boldItalic="Arial-Bold")
                return "Arial"
        except Exception:
            continue
    return "Helvetica"


def lire_reprises(cp):
    f = BASE / "reprises.csv"
    rows = list(csv.DictReader(f.open(encoding="utf-8"), delimiter=";"))
    return [r for r in rows if r.get("communique_ref") == cp and r.get("est_test") == "non"]


def link_para(url, style, color="#2E6DA4"):
    return Paragraph(f'<a href="{esc(url)}" color="{color}">{esc(url)}</a>', style)


def make_chart(categories, values, primary_color):
    d = Drawing(440, 210)
    bc = VerticalBarChart()
    bc.x = 60
    bc.y = 40
    bc.width = 340
    bc.height = 140
    bc.data = [values]
    bc.categoryAxis.categoryNames = [esc(c) for c in categories]
    bc.valueAxis.valueMin = 0
    bc.valueAxis.valueMax = (max(values) + 1) if values else 1
    bc.valueAxis.valueStep = 1
    bc.bars[0].fillColor = primary_color
    bc.barLabelFormat = "%d"
    bc.barLabels.nudge = 6
    bc.barLabels.fontSize = 9
    bc.categoryAxis.labels.fontSize = 8
    bc.valueAxis.labels.fontSize = 8
    d.add(bc)
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cp", default="CP-20261010-001")
    ap.add_argument("--config", default=str(BASE / "config" / "charte.json"))
    ap.add_argument("--out", default="")
    ap.add_argument("--titre", default="")
    ap.add_argument("--emetteur", default="")
    ap.add_argument("--date-communique", default="")
    ap.add_argument("--periode", default="")
    args = ap.parse_args()

    cfg = json.loads(pathlib.Path(args.config).read_text(encoding="utf-8"))
    fam = setup_fonts()
    coul = cfg.get("couleurs", {})
    C_P = hex2rgb(coul.get("primaire", "#1F3A5F"))
    C_S = hex2rgb(coul.get("secondaire", "#2E6DA4"))
    C_A = hex2rgb(coul.get("accent", "#C9A227"))
    C_T = hex2rgb(coul.get("texte", "#222222"))
    C_CL = hex2rgb(coul.get("texte_clair", "#FFFFFF"))
    filigrane = cfg.get("filigrane", "BROUILLON — EN ATTENTE DE VALIDATION")
    agence = cfg.get("agence", {})
    client = cfg.get("client", {})

    F = "Arial" if fam == "Arial" else "Helvetica"
    FB = "Arial-Bold" if fam == "Arial" else "Helvetica-Bold"
    FI = "Arial-Italic" if fam == "Arial" else "Helvetica-Oblique"

    # ---- styles ----
    st = {}
    st["cover_title"] = ParagraphStyle("ct", fontName=FB, fontSize=22, leading=27,
                                       textColor=C_CL, alignment=TA_LEFT)
    st["cover_sub"] = ParagraphStyle("cs", fontName=F, fontSize=12, leading=16,
                                     textColor=colors.HexColor("#cfe0f0"), alignment=TA_LEFT)
    st["h1"] = ParagraphStyle("h1", fontName=FB, fontSize=15, leading=19,
                              textColor=C_P, spaceBefore=10, spaceAfter=6)
    st["h2"] = ParagraphStyle("h2", fontName=FB, fontSize=12, leading=15,
                              textColor=C_S, spaceBefore=8, spaceAfter=4)
    st["body"] = ParagraphStyle("body", fontName=F, fontSize=9.5, leading=13,
                                textColor=C_T)
    st["small"] = ParagraphStyle("small", fontName=F, fontSize=8, leading=10,
                                 textColor=colors.HexColor("#666666"))
    st["cell"] = ParagraphStyle("cell", fontName=F, fontSize=8.5, leading=11,
                                textColor=C_T)
    st["cellb"] = ParagraphStyle("cellb", fontName=FB, fontSize=8.5, leading=11,
                                 textColor=C_T)

    # ---- données ----
    rows = lire_reprises(args.cp)
    conf = [r for r in rows if r.get("classification") == "confirmee"]
    prob = [r for r in rows if r.get("classification") == "probable"]
    nv = [r for r in rows if r.get("classification") == "non_verifiable"]
    uniques = conf + prob

    titre = args.titre or (rows[0]["titre"] if rows else "")
    emetteur = args.emetteur or agence.get("nom", "")
    date_cp = args.date_communique
    periode = args.periode
    today = "10/10/2026"

    nb_conf = len(conf)
    nb_prob = len(prob)
    nb_nv = len(nv)
    medias_uniques = len({r["media"] for r in uniques})
    pays_counts = Counter(r["pays"] for r in uniques if r.get("pays") and r["pays"] not in ("—", ""))
    pays_nd = [r for r in uniques if r.get("pays") in ("Non déterminé", "")]
    type_counts = Counter(r["type_reprise"] for r in uniques)
    type_nv = Counter(r["type_reprise"] for r in nv)

    out = args.out or str(BASE / "rapports" / f"rapport-{args.cp}.pdf")
    pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)

    def watermark(canvas, doc):
        canvas.saveState()
        canvas.translate(A4[0] / 2, A4[1] / 2)
        canvas.rotate(45)
        canvas.setFont(FB, 36)
        canvas.setFillAlpha(0.12)
        canvas.setFillColor(colors.grey)
        canvas.drawCentredString(0, 0, filigrane)
        canvas.restoreState()

    doc = SimpleDocTemplate(out, pagesize=A4,
                            leftMargin=1.6 * cm, rightMargin=1.6 * cm,
                            topMargin=1.6 * cm, bottomMargin=1.6 * cm,
                            title=titre, author=agence.get("nom", ""))
    story = []

    # ================= COUVERTURE =================
    band = Table([[Paragraph(esc(agence.get("nom", "")), st["cover_title"])],
                  [Paragraph(esc("Rapport de couverture médiatique"), st["cover_sub"])]],
                 colWidths=[doc.width])
    band.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_P),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("TOPPADDING", (0, 0), (-1, -1), 18),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 18),
    ]))
    story.append(band)
    story.append(Spacer(1, 1.2 * cm))

    if client.get("nom"):
        story.append(Paragraph(esc("Préparé pour : " + client["nom"]), st["body"]))
        story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(esc("Communiqué de presse"), st["h2"]))
    story.append(Paragraph(esc(titre), ParagraphStyle("tt", fontName=FB, fontSize=16, leading=20, textColor=C_T)))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(esc("Émetteur : " + emetteur), st["body"]))
    if date_cp:
        story.append(Paragraph(esc("Date du communiqué : " + date_cp), st["body"]))
    if periode:
        story.append(Paragraph(esc("Période de monitoring : " + periode), st["body"]))
    story.append(Paragraph(esc("Date du rapport : " + today), st["body"]))
    story.append(Spacer(1, 0.8 * cm))

    badge = Table([[Paragraph(esc(filigrane), ParagraphStyle("bd", fontName=FB, fontSize=12, leading=15, textColor=colors.HexColor("#8a6d00"), alignment=TA_CENTER))]],
                  colWidths=[doc.width])
    badge.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fdf3d1")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#c9a227")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(badge)
    story.append(PageBreak())

    # ================= EXECUTIVE SUMMARY =================
    story.append(Paragraph("Executive Summary", st["h1"]))
    story.append(Paragraph(esc(
        "Ce rapport présente la couverture médiatique du communiqué de presse « " + titre +
        " ». Il est établi exclusivement à partir des reprises vérifiées enregistrées "
        "dans le registre du MEDIA MONITORING AGENT."), st["body"]))
    story.append(Spacer(1, 0.4 * cm))

    kpi = [
        [Paragraph("Reprises confirmées", st["cellb"]), Paragraph(str(nb_conf), st["cell"])],
        [Paragraph("Reprises probables", st["cellb"]), Paragraph(str(nb_prob), st["cell"])],
        [Paragraph("Publications non vérifiées", st["cellb"]), Paragraph(str(nb_nv), st["cell"])],
        [Paragraph("Médias uniques", st["cellb"]), Paragraph(str(medias_uniques), st["cell"])],
        [Paragraph("Pays identifiés", st["cellb"]), Paragraph(str(len(pays_counts)), st["cell"])],
        [Paragraph("Langues", st["cellb"]), Paragraph("Français", st["cell"])],
    ]
    t_kpi = Table(kpi, colWidths=[doc.width * 0.55, doc.width * 0.45])
    t_kpi.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d7e0")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f4f8")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_kpi)
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("Synthèse qualitative", st["h2"]))
    story.append(Paragraph(esc(
        "Les reprises confirmées sont des reprises intégrales du communiqué, conformes au "
        "modèle de distribution d'African Media Agency : le texte complet est repris à "
        "l'identique par des médias partenaires. Aucune reprise partielle, reformulée ou "
        "traduite n'a été détectée à ce jour."), st["body"]))

    # ================= MEDIA COVERAGE =================
    story.append(PageBreak())
    story.append(Paragraph("Media Coverage", st["h1"]))
    entete = [Paragraph(h, st["cellb"]) for h in ["Média", "Pays", "Titre", "Date", "Statut", "URL"]]
    data = [entete]
    for r in conf + prob:
        statut_txt = "Confirmée" if r.get("classification") == "confirmee" else "Probable"
        data.append([
            Paragraph(esc(r["media"]), st["cell"]),
            Paragraph(esc(r["pays"] or "—"), st["cell"]),
            Paragraph(esc(r["titre"]), st["cell"]),
            Paragraph(esc(r.get("date_publication") or "n/d"), st["cell"]),
            Paragraph(esc(statut_txt), st["cell"]),
            link_para(r["url"], st["cell"], "#2E6DA4"),
        ])
    t_mc = Table(data, colWidths=[doc.width * 0.15, doc.width * 0.12, doc.width * 0.28,
                                  doc.width * 0.10, doc.width * 0.10, doc.width * 0.25],
                 repeatRows=1)
    t_mc.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_P),
        ("TEXTCOLOR", (0, 0), (-1, 0), C_CL),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c9d2dc")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f8fb")]),
    ]))
    story.append(t_mc)

    if nv:
        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph("Publications non vérifiées (hors reprises confirmées)", st["h2"]))
        for r in nv:
            story.append(Paragraph(
                f"• {esc(r['media'])} ({esc(r.get('type_reprise', '') or 'mention')}) — {esc(r.get('note', ''))}",
                st["body"]))
            story.append(link_para(r["url"], st["body"]))

    # ================= GEOGRAPHIC COVERAGE =================
    story.append(PageBreak())
    story.append(Paragraph("Geographic Coverage", st["h1"]))
    if pays_counts:
        cats = list(pays_counts.keys())
        vals = [pays_counts[c] for c in cats]
        story.append(make_chart(cats, vals, C_S))
        story.append(Spacer(1, 0.3 * cm))
        geo_rows = [[Paragraph("Pays", st["cellb"]), Paragraph("Reprises", st["cellb"])]]
        for c, v in pays_counts.most_common():
            geo_rows.append([Paragraph(esc(c), st["cell"]), Paragraph(str(v), st["cell"])])
        t_geo = Table(geo_rows, colWidths=[doc.width * 0.6, doc.width * 0.4])
        t_geo.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c9d2dc")),
            ("BACKGROUND", (0, 0), (-1, 0), C_P),
            ("TEXTCOLOR", (0, 0), (-1, 0), C_CL),
        ]))
        story.append(t_geo)
    if pays_nd:
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph("Pays non déterminés", st["h2"]))
        for r in pays_nd:
            story.append(Paragraph(f"• {esc(r['media'])}", st["body"]))
    else:
        story.append(Paragraph("Aucune reprise avec pays identifié.", st["body"]))

    # ================= COVERAGE ANALYSIS =================
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("Coverage Analysis", st["h1"]))
    story.append(Paragraph("Répartition par type de reprise", st["h2"]))
    type_rows = [[Paragraph("Type", st["cellb"]), Paragraph("Nombre", st["cellb"])]]
    for t, v in type_counts.most_common():
        label = {"reprise_integrale": "Reprise intégrale", "reprise_partielle": "Reprise partielle",
                 "adaptation": "Reformulée", "traduction": "Traduite", "citation": "Citation",
                 "mention": "Mention", "syndication": "Syndication"}.get(t, t)
        type_rows.append([Paragraph(esc(label), st["cell"]), Paragraph(str(v), st["cell"])])
    if type_nv:
        type_rows.append([Paragraph("Non vérifiées (mention vidéo)", st["cell"]),
                          Paragraph(str(sum(type_nv.values())), st["cell"])])
    t_ty = Table(type_rows, colWidths=[doc.width * 0.6, doc.width * 0.4])
    t_ty.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c9d2dc")),
                              ("BACKGROUND", (0, 0), (-1, 0), C_P),
                              ("TEXTCOLOR", (0, 0), (-1, 0), C_CL)]))
    story.append(t_ty)

    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("Langue", st["h2"]))
    story.append(Paragraph("Français — 100 % des reprises vérifiées sont en français.", st["body"]))

    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("Chronologie des publications", st["h2"]))
    tri = sorted(uniques, key=lambda r: r.get("date_publication") or "9999")
    for r in tri:
        d = r.get("date_publication") or "n/d"
        story.append(Paragraph(f"• {esc(d)} — {esc(r['media'])}", st["body"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("Analyse qualitative", st["h2"]))
    story.append(Paragraph(esc(
        "La couverture est homogène : les médias reprennent le texte du communiqué sans "
        "modification d'angle éditorial, ce qui reflète une diffusion fidèle du message. "
        "La répartition géographique montre une dominante ouest-africaine (Côte d'Ivoire) "
        "avec une reprise en Afrique du Sud et une en RDC."), st["body"]))

    # ================= KEY INSIGHTS =================
    story.append(PageBreak())
    story.append(Paragraph("Key Insights &amp; Recommendations", st["h1"]))
    insights = []
    insights.append(f"{nb_conf} média(s) ont repris intégralement le communiqué, sans reformulation.")
    if pays_counts:
        top = pays_counts.most_common(1)[0]
        insights.append(f"Le pays le plus représenté est {top[0]} ({top[1]} reprise(s)).")
    if medias_uniques:
        insights.append(f"{medias_uniques} média(s) unique(s) ont relayé le message.")
    if nb_nv:
        insights.append(f"{nb_nv} publication(s) n'ont pas pu être vérifiée(s) (signalées séparément).")
    for i, ins in enumerate(insights, 1):
        story.append(Paragraph(f"<b>{i}.</b> {esc(ins)}", st["body"]))
        story.append(Spacer(1, 0.15 * cm))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Recommandations", st["h2"]))
    story.append(Paragraph(esc(
        "Poursuivre le monitoring périodique (J+1, J+2, J+3, J+7) pour identifier de nouvelles "
        "reprises ; confirmer le pays du média Farafina News ; suivre l'éventuelle émergence de "
        "reprises anglophones."), st["body"]))

    # ================= METHODOLOGY =================
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("Methodology &amp; Limitations", st["h1"]))
    story.append(Paragraph("Méthodologie", st["h2"]))
    story.append(Paragraph(esc(
        "Recherche web (web_search, backends multiples) en français et en anglais : titre exact, "
        "variantes, phrases distinctives et mots-clés. Vérification de chaque URL par ouverture "
        "réelle (browser_exec) : titre, date et correspondance du contenu avec le communiqué. "
        "Déduplication par titre normalisé et média."), st["body"]))
    story.append(Paragraph("Critères de vérification", st["h2"]))
    story.append(Paragraph(esc(
        "Confirmée : URL ouverte et contenu effectivement lié au communiqué. "
        "Probable : contenu confirmé via l'index de recherche, page non ouverte en direct. "
        "Non vérifiable : page inaccessible ou vidéo indisponible."), st["body"]))
    story.append(Paragraph("Limites", st["h2"]))
    story.append(Paragraph(esc(
        "Les articles consacrés au « Rapport Sécurité Yango Ride 2024-2025 » (communication "
        "distincte) sont exclus. Une page (Matin Infos) n'a pas pu être ouverte en direct. "
        "Le pays d'un média (Farafina News) reste non déterminé. Aucune reprise anglophone n'a "
        "été détectée."), st["body"]))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(esc("Rapport généré le " + today + " — " + filigrane), st["small"]))

    doc.build(story, onFirstPage=watermark, onLaterPages=watermark)
    print(f"PDF généré : {out}")
    print(f"  confirmées={nb_conf}, probables={nb_prob}, non_vérifiées={nb_nv}, médias={medias_uniques}")


if __name__ == "__main__":
    main()
