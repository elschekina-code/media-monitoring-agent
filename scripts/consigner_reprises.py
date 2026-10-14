# -*- coding: utf-8 -*-
"""
Consignation des reprises RÉELLES — MEDIA MONITORING AGENT (V1)

Usage :  python scripts/consigner_reprises.py <chemin_vers_input.json>

Lit un fichier JSON décrivant le communiqué analysé et les reprises VÉRIFIÉES,
attribue les identifiants réels (CP-…, REP-…), applique la déduplication,
écrit dans reprises.csv / journal.csv avec est_test=non, et génère le rapport
professionnel dans rapports/.

Aucune dépendance : bibliothèque standard uniquement.
Les données de test (est_test=oui) ne sont jamais touchées ni comptées.
"""
import csv
import datetime
import json
import pathlib
import re
import sys

BASE = pathlib.Path(r"C:/Users/MICROSOFT/Documents/media-monitoring-agent")
REPRISES = BASE / "reprises.csv"
JOURNAL = BASE / "journal.csv"
RAPPORTS = BASE / "rapports"
RAPPORTS.mkdir(exist_ok=True)

STOP = {"le", "la", "les", "de", "du", "des", "et", "sa", "son", "ses",
        "a", "au", "aux", "un", "une", "the", "of", "and", "for", "in", "on"}


def normalise(titre: str) -> str:
    t = titre.lower()
    t = re.sub(r"[^\w\s]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return " ".join(m for m in t.split() if m not in STOP)


def _classification(r: dict) -> str:
    if r.get("classification"):
        return r["classification"]
    if r.get("statut_verification") == "non_verifie":
        return "non_verifiable"
    if "probable" in r.get("note", "").lower():
        return "probable"
    return "confirmee"


def lire_ids_existants():
    """Retourne (max_rep, max_cp) pour la numérotation incrémentale par jour."""
    jour = datetime.date.today().strftime("%Y%m%d")
    rep_max = 0
    cp_max = 0
    if REPRISES.exists():
        for r in csv.DictReader(REPRISES.open(encoding="utf-8"), delimiter=";"):
            m = re.fullmatch(r"REP-(\d{8})-(\d{3})", r.get("id", ""))
            if m and m.group(1) == jour:
                rep_max = max(rep_max, int(m.group(2)))
    if JOURNAL.exists():
        for j in csv.DictReader(JOURNAL.open(encoding="utf-8"), delimiter=";"):
            m = re.fullmatch(r"CP-(\d{8})-(\d{3})", j.get("communique_ref", ""))
            if m and m.group(1) == jour:
                cp_max = max(cp_max, int(m.group(2)))
    return rep_max, cp_max


def main():
    if len(sys.argv) != 2:
        print("Usage : python scripts/consigner_reprises.py <input.json>")
        sys.exit(1)

    data = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    cp = data["communique"]
    reprises = data["reprises"]
    meta = data.get("rapport", {})
    jour = datetime.date.today()

    rep_max, cp_max = lire_ids_existants()
    cp_id = f"CP-{jour:%Y%m%d}-{cp_max + 1:03d}"

    # --- déduplication dans le lot + contrôle des URLs déjà collectées ----
    urls_existantes = set()
    if REPRISES.exists():
        urls_existantes = {r["url"].strip() for r in
                           csv.DictReader(REPRISES.open(encoding="utf-8"), delimiter=";")
                           if r.get("est_test") != "oui"}

    vus, lignes = {}, []
    for r in reprises:
        url = r["url"].strip()
        if url in urls_existantes:
            r["_deja_collecte"] = True
            continue
        cle = (normalise(r["titre"]), r["media"].lower())
        if cle in vus:
            r["note"] = (r.get("note", "") + f" doublon_de={vus[cle]}").strip()
            r["type_reprise"] = "syndication"
        else:
            vus[cle] = None  # attribué ci-dessous
        lignes.append(r)
        urls_existantes.add(url)

    # --- attribution des identifiants réels ---
    rep_ids = {}
    n = rep_max
    for r in lignes:
        n += 1
        rid = f"REP-{jour:%Y%m%d}-{n:03d}"
        r["id"] = rid
        rep_ids[(normalise(r["titre"]), r["media"].lower())] = rid
    # corrige les références doublon_de (2e passe)
    for r in lignes:
        if "doublon_de=" in r.get("note", ""):
            cle = (normalise(r["titre"]), r["media"].lower())
            r["note"] = r["note"].replace("doublon_de=None",
                                          f"doublon_de={rep_ids.get(cle, '?')}")

    # --- écriture reprises.csv (est_test=non) ---
    with REPRISES.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        for r in lignes:
            w.writerow([
                r["id"], cp_id, r["media"], r["pays"], r["titre"],
                r.get("date_publication", ""), r["url"], r["type_reprise"],
                r.get("source_recherche", ""), r.get("statut_verification", "verifie"),
                _classification(r),
                jour.isoformat(), "non", r.get("note", ""),
            ])

    # --- écriture journal.csv ---
    lignes_journal = [
        (f"JRN-{jour:%Y%m%d}-{cp_max + 1:03d}-ANA", jour.isoformat(), cp_id,
         "analyse_communique",
         f"url={cp['url']}; titre={cp.get('titre', '')}; emetteur={cp.get('emetteur', '')}",
         "ok", ""),
        (f"JRN-{jour:%Y%m%d}-{cp_max + 1:03d}-RECH", jour.isoformat(), cp_id,
         "recherche_reprises",
         f"{len(lignes)} reprises vérifiées + {sum(1 for r in reprises if r.get('_deja_collecte'))} déjà collectée(s)",
         "ok", ""),
    ]
    for r in lignes:
        lignes_journal.append((
            f"JRN-{jour:%Y%m%d}-{cp_max + 1:03d}-{r['id'].split('-')[-1]}",
            jour.isoformat(), cp_id, "enregistrement",
            f"reprise {r['id']} {r['media']} ({r['type_reprise']})", "ok", ""))
    with JOURNAL.open("a", newline="", encoding="utf-8") as f:
        csv.writer(f, delimiter=";").writerows(lignes_journal)

    # --- statistiques pour le rapport ---
    total = len(lignes)
    nb_doublons = sum(1 for r in lignes if "doublon_de=" in r.get("note", ""))
    uniques = [r for r in lignes if "doublon_de=" not in r.get("note", "")]
    nb_medias = len({r["media"] for r in uniques})
    par_type = {}
    for r in uniques:
        par_type[r["type_reprise"]] = par_type.get(r["type_reprise"], 0) + 1
    par_pays = {}
    for r in uniques:
        par_pays[r["pays"]] = par_pays.get(r["pays"], 0) + 1
    non_verifiables = [r for r in uniques
                       if r.get("statut_verification") in ("inaccessible", "non_verifie")]

    table = "\n".join(
        f"| {r['id']} | {r['media']} | {r['pays']} | {r['titre']} | "
        f"{r.get('date_publication','')} | {r['type_reprise']} | {r['url']} |"
        for r in uniques
    )
    if non_verifiables:
        nv_table = "\n".join(f"- {r['media']} — {r['url']}" for r in non_verifiables)
    else:
        nv_table = "—"

    rapport = f"""# Rapport de monitoring — {cp.get('titre', '')}

- **Communiqué** : `{cp_id}` — [{cp.get('titre', '')}]({cp['url']})
- **Émetteur** : {cp.get('emetteur', '')}
- **Date du communiqué** : {cp.get('date', '')}
- **Date d'analyse** : {jour.isoformat()}

## Méthodologie
{meta.get('methode', '')}

## Synthèse quantitative
- Reprises uniques vérifiées : **{len(uniques)}**
- Doublons détectés (non comptés) : {nb_doublons}
- Médias distincts : {nb_medias}
- Répartition par type : {par_type}
- Répartition par pays : {par_pays}

## Synthèse qualitative
{meta.get('synthese_qualitative', '')}

## Tableau détaillé des reprises
| id | média | pays | titre | date | type | URL |
|---|---|---|---|---|---|---|
{table}

## Publications non vérifiables
{nv_table}

## Limites
{meta.get('limites', '')}

## Prochaines actions
{meta.get('prochaines_actions', '')}
"""
    rapport_path = RAPPORTS / f"rapport-{cp_id}.md"
    rapport_path.write_text(rapport, encoding="utf-8")

    print(f"Communiqué : {cp_id}")
    print(f"Reprises uniques écrites : {len(uniques)} | doublons : {nb_doublons} "
          f"| déjà collectées : {sum(1 for r in reprises if r.get('_deja_collecte'))}")
    print(f"Médias distincts : {nb_medias} | non vérifiables : {len(non_verifiables)}")
    print(f"Rapport : {rapport_path}")


if __name__ == "__main__":
    main()
