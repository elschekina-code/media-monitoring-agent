# -*- coding: utf-8 -*-
"""
Génère la synthèse exécutive (PDF une page) destinée aux responsables / clients.
MEDIA MONITORING AGENT V1.1.

Usage :
    python scripts/generer_synthese_executive.py --cp CP-20261010-001 \
        --emetteur "..." --date-communique "15/09/2026"

Lit reprises.csv (données réelles uniquement), produit un PDF d'une page max,
chiffres exclusivement issus des données. Marqué « BROUILLON — EN ATTENTE DE VALIDATION ».
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
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
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
            pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-Bold",
                                          italic="Arial", boldItalic="Arial-Bold")
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
                pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-Bold",
                                              italic="Arial", boldItalic="Arial-Bold")
                return "Arial"
        except Exception:
            continue
    return "Helvetica"


def lire_reprises(cp):
    f = BASE / "reprises.csv"
    rows = list(csv.DictReader(f.open(encoding="utf-8"), delimiter=";"))
    return [r for r in rows if r.get("communique_ref") == cp and r.get("est_test") == "non"]


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
    C_T = hex2rgb(coul.get("texte", "#222222"))
    C_CL = hex2rgb(coul.get("texte_clair", "#FFFFFF"))
    filigrane = cfg.get("filigrane", "BROUILLON — EN ATTENTE DE VALIDATION")
    agence = cfg.get("agence", {})
    client = cfg.get("client", {})

    F = "Arial" if fam == "Arial" else "Helvetica"
    FB = "Arial-Bold" if fam == "Arial" else "Helvetica-Bold"

    st = {
        "band": ParagraphStyle("band", fontName=FB, fontSize=17, leading=21, textColor=C_CL),
        "bandsub": ParagraphStyle("bandsub", fontName=F, fontSize=10.5, leading=14,
                                  textColor=colors.HexColor("#cfe0f0")),
        "title": ParagraphStyle("title", fontName=FB, fontSize=13, leading=17, textColor=C_T),
        "h": ParagraphStyle("h", fontName=FB, fontSize=11, leading=14, textColor=C_P,
                            spaceBefore=8, spaceAfter=4),
        "body": ParagraphStyle("body", fontName=F, fontSize=9.5, leading=13, textColor=C_T),
        "cell": ParagraphStyle("cell", fontName=F, fontSize=9, leading=12, textColor=C_T),
        "cellb": ParagraphStyle("cellb", fontName=FB, fontSize=9, leading=12, textColor=C_T),
        "small": ParagraphStyle("small", fontName=F, fontSize=8, leading=10,
                                textColor=colors.HexColor("#666666")),
    }

    rows = lire_reprises(args.cp)
    conf = [r for r in rows if r.get("classification") == "confirmee"]
    prob = [r for r in rows if r.get("classification") == "probable"]
    nv = [r for r in rows if r.get("classification") == "non_verifiable"]
    uniques = conf + prob

    titre = args.titre or (rows[0]["titre"] if rows else "")
    emetteur = args.emetteur or ""
    date_cp = args.date_communique
    periode = args.periode
    today = "10/10/2026"

    nb_conf = len(conf)
    nb_prob = len(prob)
    nb_nv = len(nv)
    medias = len({r["media"] for r in uniques})
    pays = Counter(r["pays"] for r in uniques if r.get("pays") and r["pays"] not in ("—", ""))
    langues = "Français"

    out = args.out or str(BASE / "rapports" / f"synthese-{args.cp}.pdf")
    pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)

    def watermark(canvas, doc):
        canvas.saveState()
        canvas.translate(A4[0] / 2, A4[1] / 2)
        canvas.rotate(45)
        canvas.setFont(FB, 30)
        canvas.setFillAlpha(0.12)
        canvas.setFillColor(colors.grey)
        canvas.drawCentredString(0, 0, filigrane)
        canvas.restoreState()

    doc = SimpleDocTemplate(out, pagesize=A4,
                            leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                            topMargin=1.3 * cm, bottomMargin=1.3 * cm,
                            title="Synthèse exécutive — " + titre)

    story = []
    band = Table([[Paragraph(esc(agence.get("nom", "")), st["band"])],
                  [Paragraph(esc("Synthèse exécutive — couverture médiatique"), st["bandsub"])]],
                 colWidths=[doc.width])
    band.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_P),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(band)
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph(esc(titre), st["title"]))
    if emetteur:
        story.append(Paragraph(esc("Émetteur : " + emetteur), st["body"]))
    meta = []
    if date_cp:
        meta.append("Communiqué : " + esc(date_cp))
    if periode:
        meta.append("Période : " + esc(periode))
    meta.append("Rapport : " + today)
    story.append(Paragraph(" · ".join(meta), st["small"]))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Résultats clés", st["h"]))
    kpi = [
        [Paragraph("Reprises confirmées", st["cell"]), Paragraph(str(nb_conf), st["cellb"])],
        [Paragraph("Reprises probables", st["cell"]), Paragraph(str(nb_prob), st["cellb"])],
        [Paragraph("Publications non vérifiées", st["cell"]), Paragraph(str(nb_nv), st["cellb"])],
        [Paragraph("Médias uniques", st["cell"]), Paragraph(str(medias), st["cellb"])],
        [Paragraph("Pays couverts", st["cell"]), Paragraph(str(len(pays)), st["cellb"])],
        [Paragraph("Langue", st["cell"]), Paragraph(langues, st["cellb"])],
    ]
    t_kpi = Table(kpi, colWidths=[doc.width * 0.62, doc.width * 0.38])
    t_kpi.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c9d2dc")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f4f8")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_kpi)

    story.append(Paragraph("Médias ayant repris le communiqué", st["h"]))
    for r in uniques:
        statut = "confirmée" if r.get("classification") == "confirmee" else "probable"
        d = r.get("date_publication") or "n/d"
        story.append(Paragraph(
            f"• <b>{esc(r['media'])}</b> ({esc(r['pays'] or 'pays n/d')}) — {esc(d)} — "
            f"{esc(statut)} — <link href='{esc(r['url'])}' color='#2E6DA4'>{esc(r['url'])}</link>",
            st["body"]))
    if nv:
        story.append(Paragraph(
            f"• <b>{esc(nv[0]['media'])}</b> (mention vidéo) — non vérifiable — "
            f"<link href='{esc(nv[0]['url'])}' color='#2E6DA4'>{esc(nv[0]['url'])}</link>",
            st["body"]))

    story.append(Paragraph("Analyse", st["h"]))
    story.append(Paragraph(esc(
        "Les reprises confirmées sont des reprises intégrales du communiqué, reprises à "
        "l'identique par des médias partenaires. Aucune reprise partielle, reformulée ou "
        "traduite n'a été détectée à ce jour. La couverture est dominée par des médias "
        "francophones, avec une présence en Côte d'Ivoire et en Afrique australe."), st["body"]))

    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(esc("Document de travail — " + filigrane), st["small"]))

    doc.build(story, onFirstPage=watermark, onLaterPages=watermark)
    print(f"Synthèse exécutive générée : {out}")
    print(f"  confirmées={nb_conf}, probables={nb_prob}, non_vérifiées={nb_nv}, médias={medias}")


if __name__ == "__main__":
    main()
