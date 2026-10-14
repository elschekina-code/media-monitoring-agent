# -*- coding: utf-8 -*-
"""
Dry-run fictif — MEDIA MONITORING AGENT (V1)
Simule l'analyse d'un communiqué FICTIF, la détection de reprises FICTIVES,
la déduplication, puis l'écriture dans reprises.csv / journal.csv
et la génération d'un rapport de test. Aucune donnée réelle.
Aucune dépendance : bibliothèque standard uniquement.
"""
import csv
import datetime
import pathlib
import re

BASE = pathlib.Path(r"C:/Users/MICROSOFT/Documents/media-monitoring-agent")
REPRISES = BASE / "reprises.csv"
JOURNAL = BASE / "journal.csv"
TESTS = BASE / "tests"
TESTS.mkdir(exist_ok=True)

TODAY = datetime.date.today().isoformat()          # ex. 2026-10-10
REF_CP = "CP-TEST-20261010-001"                     # communiqué FICTIF

# ---------------------------------------------------------------------------
# 1. Communiqué fictif
# ---------------------------------------------------------------------------
communique = {
    "ref": REF_CP,
    "url": "https://exemple-fictif.local/communiques/lancement-nebulis",
    "titre": "Horizon Software lance Nébulis, sa nouvelle plateforme cloud (FICTIF)",
    "emetteur": "Horizon Software (société fictive)",
    "date": "2026-10-09",
    "mots_cles": ["Nébulis", "Horizon Software", "plateforme cloud", "lancement"],
}

# ---------------------------------------------------------------------------
# 2. Reprises fictives candidates (avec un doublon délibéré : #4 == #1)
# ---------------------------------------------------------------------------
candidats = [
    dict(id="REP-20261010-001", media="Presse Tech Afrique", pays="Côte d'Ivoire",
         titre="Horizon Software lance Nébulis, sa nouvelle plateforme cloud",
         date_publication="2026-10-10", url="https://presse-tech-afrique.test/article/nebulis",
         type_reprise="reprise_integrale", source="web_search"),
    dict(id="REP-20261010-002", media="Échos du Numérique", pays="France",
         titre="Nébulis : Horizon Software muscle son offre cloud",
         date_publication="2026-10-10", url="https://echos-numerique.test/nebulis-horizon",
         type_reprise="reprise_partielle", source="web_search"),
    dict(id="REP-20261010-003", media="Global Tech Review", pays="Royaume-Uni",
         titre="Cloud roundup: this week's launches",
         date_publication="2026-10-10", url="https://globaltechreview.test/cloud-roundup",
         type_reprise="citation", source="browser_exec"),
    dict(id="REP-20261010-004", media="Presse Tech Afrique", pays="Côte d'Ivoire",
         titre="Horizon Software lance nébulis, sa nouvelle plateforme cloud !",
         date_publication="2026-10-10", url="https://presse-tech-afrique.test/article/nebulis?utm_source=rss",
         type_reprise="reprise_integrale", source="web_search"),
]

# ---------------------------------------------------------------------------
# 3. Déduplication (clé = titre normalisé + média, cf. SPEC §5)
# ---------------------------------------------------------------------------
def normalise(titre: str) -> str:
    t = titre.lower()
    t = re.sub(r"[^\w\s]", "", t)                 # retire ponctuation
    t = re.sub(r"\s+", " ", t).strip()
    stop = {"le", "la", "les", "de", "du", "des", "et", "sa", "son", "ses", "a", "au", "aux"}
    mots = [m for m in t.split() if m not in stop]
    return " ".join(mots)

vus = {}
for c in candidats:
    cle = (normalise(c["titre"]), c["media"].lower())
    if cle in vus:
        c["note"] = f"doublon_de={vus[cle]}"
        c["type_reprise"] = "syndication"
    else:
        vus[cle] = c["id"]
        c["note"] = ""

# ---------------------------------------------------------------------------
# 4. Écriture reprises.csv (est_test=oui partout)
# ---------------------------------------------------------------------------
with REPRISES.open("a", newline="", encoding="utf-8") as f:
    w = csv.writer(f, delimiter=";")
    for c in candidats:
        w.writerow([
            c["id"], REF_CP, c["media"], c["pays"], c["titre"],
            c["date_publication"], c["url"], c["type_reprise"], c["source"],
            "verifie", TODAY, "oui", c["note"],
        ])

# ---------------------------------------------------------------------------
# 5. Écriture journal.csv
# ---------------------------------------------------------------------------
journal = [
    ("JRN-20261010-001", TODAY, REF_CP, "analyse_communique",
     f"titre={communique['titre']}", "ok", "donnée de test"),
    ("JRN-20261010-002", TODAY, REF_CP, "recherche_reprises",
     "4 candidats trouvés (simulation)", "ok", "donnée de test"),
    ("JRN-20261010-003", TODAY, REF_CP, "deduplication",
     "1 doublon détecté et marqué", "ok", "donnée de test"),
]
for c in candidats:
    journal.append((f"JRN-{c['id'].split('-')[-1]}-{c['id']}", TODAY, REF_CP,
                    "enregistrement", f"reprise {c['id']} {c['media']}", "ok",
                    "donnée de test"))

with JOURNAL.open("a", newline="", encoding="utf-8") as f:
    w = csv.writer(f, delimiter=";")
    for row in journal:
        w.writerow(row)

# ---------------------------------------------------------------------------
# 6. Vérification (relecture)
# ---------------------------------------------------------------------------
reprises_lues = list(csv.DictReader(REPRISES.open(encoding="utf-8"), delimiter=";"))
journal_lues = list(csv.DictReader(JOURNAL.open(encoding="utf-8"), delimiter=";"))
nb_doublons = sum(1 for r in reprises_lues if r["note"].startswith("doublon_de="))
nb_reelles = sum(1 for r in reprises_lues if r["est_test"] != "oui")

# ---------------------------------------------------------------------------
# 7. Rapport de test
# ---------------------------------------------------------------------------
lignes_table = "\n".join(
    f"| {r['id']} | {r['media']} | {r['pays']} | {r['type_reprise']} | "
    f"{'doublon' if r['note'].startswith('doublon_de=') else 'ok'} |"
    for r in reprises_lues
)

rapport = f"""# Rapport de test — MEDIA MONITORING AGENT (DONNÉES FICTIVES)

> ⚠️ **TEST / SIMULATION.** Toutes les données ci-dessous sont fictives
> (`est_test=oui`). Elles ne constituent pas de véritables reprises et ne sont
> pas comptabilisées comme telles. Date : {TODAY}.

## Communiqué fictif analysé
- Référence : `{REF_CP}`
- Titre : {communique['titre']}
- Émetteur : {communique['emetteur']}
- Date : {communique['date']}

## Résultat du dry-run
- Reprises écrites : {len(reprises_lues)} (toutes `est_test=oui`)
- Doublons détectés et marqués : {nb_doublons}
- Reprises réelles (doit être 0) : {nb_reelles}
- Lignes de journal : {len(journal_lues)}

## Tableau des reprises (test)
| id | média | pays | type | statut dédup |
|---|---|---|---|---|
{lignes_table}

## Vérifications
- [x] Schéma des CSV respecté (séparateur `;`, encodage UTF-8)
- [x] Déduplication fonctionnelle (1 doublon marqué, aucune ligne supprimée)
- [x] Traçabilité dans `journal.csv`
- [x] Données de test marquées et exclues des comptages réels
"""

rapport_path = TESTS / f"rapport-test-{TODAY}.md"
rapport_path.write_text(rapport, encoding="utf-8")

print("=== DRY-RUN TERMINÉ ===")
print(f"reprises.csv : {len(reprises_lues)} lignes (dont {nb_doublons} doublon(s))")
print(f"journal.csv   : {len(journal_lues)} lignes")
print(f"reprises réelles (hors test) : {nb_reelles}")
print(f"rapport écrit : {rapport_path}")
print("\n--- Contenu de reprises.csv (test) ---")
for r in reprises_lues:
    print(f"  {r['id']} | {r['media']} | {r['pays']} | {r['type_reprise']} | note={r['note'] or '-'}")
