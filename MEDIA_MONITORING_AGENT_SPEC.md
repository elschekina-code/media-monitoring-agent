# MEDIA MONITORING AGENT — Spécification technique (SPEC)

## 1. Fichiers de données

| Fichier | Rôle | Séparateur | Encodage |
|---|---|---|---|
| `reprises.csv` | Tableau des reprises détectées | `;` | UTF-8 |
| `journal.csv` | Traçabilité des actions | `;` | UTF-8 |

Toute cellule contenant un `;` ou un saut de ligne doit être encadrée de guillemets doubles `"` (les guillemets internes doublés).

## 2. Tableau des reprises — `reprises.csv`

| Colonne | Type | Description | Obligatoire |
|---|---|---|---|
| `id` | texte | Identifiant stable de la reprise, format `REP-YYYYMMDD-NNN` | oui |
| `communique_ref` | texte | Référence du communiqué analysé : `CP-YYYYMMDD-NNN` ou URL source | oui |
| `media` | texte | Nom du média / plateforme | oui |
| `pays` | texte | Pays du média | oui |
| `titre` | texte | Titre de l'article / reprise | oui |
| `date_publication` | date | Date de publication de la reprise (`AAAA-MM-JJ`) | oui si connue |
| `url` | texte | URL canonique vérifiée de la reprise | oui |
| `type_reprise` | enum | Voir §4 | oui |
| `source_recherche` | texte | Outil/méthode de découverte (`web_search`, `browser_exec`, ...) | oui |
| `statut_verification` | enum | Voir §3 | oui |
| `classification` | enum | `confirmee` / `probable` / `non_verifiable` (contrôle qualité) | oui |
| `date_collecte` | date | Date de collecte (`AAAA-MM-JJ`) | oui |
| `est_test` | bool | `oui` / `non` | oui |
| `note` | texte | Remarque libre (dédoublonnage, paywall, etc.) | non |

## 3. Statuts de vérification

| Statut | Signification |
|---|---|
| `a_verifier` | URL candidate trouvée, contenu pas encore ouvert |
| `verifie` | URL accessible ET contenu effectivement lié au communiqué |
| `inaccessible` | URL introuvable, paywall, erreur de chargement |
| `non_verifie` | Vérification non effectuée (outil indisponible ou hors périmètre) |

## 4. Types de reprise

| Type | Définition |
|---|---|
| `reprise_integrale` | Publication intégrale (ou quasi intégrale) du communiqué |
| `reprise_partielle` | Reprise substantielle d'extraits (plusieurs paragraphes) |
| `citation` | Citation courte du communiqué dans un article plus large |
| `mention` | Simple mention du sujet / de l'émetteur, sans reprise de contenu |
| `adaptation` | Réécriture éditoriale du contenu du communiqué |
| `traduction` | Reprise traduite du communiqué dans une autre langue |
| `syndication` | Reprise automatisée via fil de dépêche (AFP, agences...) |

## 5. Règles de déduplication

- **Clé de déduplication** = titre normalisé (minuscules, sans ponctuation, sans mots vides) + média. Deux lignes de même clé = une seule reprise.
- Une même dépêche reprise par plusieurs sites = **une seule reprise** (média = premier diffuseur identifié ; les relais sont listés en `note`).
- Variantes d'URL (`?utm_...`, slash final, `m.` mobile) → normalisées vers l'URL canonique.
- **On ne supprime jamais une ligne.** Un doublon est marqué en `note` : `doublon_de=<id>` et conservé pour traçabilité.

## 6. Identifiants

- Communiqué : `CP-YYYYMMDD-NNN` (consigné dans `journal.csv` à l'analyse).
- Reprise : `REP-YYYYMMDD-NNN` (incrément séquentiel par jour).

## 7. Données de test et données réelles

- Toute ligne de test porte `est_test=oui` ; toute ligne réelle porte `est_test=non`.
- Les comptages et synthèses réels excluent systématiquement `est_test=oui`.
- Les rapports de test vivent dans `tests/` ; les rapports de monitoring réel vivent dans `rapports/`.
- Les données de test et les données réelles ne sont jamais mélangées dans un même rapport.

## 8. Cohérence attendue

- `id` unique dans chaque CSV.
- Toute reprise référence un `communique_ref` déjà consigné dans `journal.csv`.
- Toute action d'écriture est doublée d'une ligne de `journal.csv`.
