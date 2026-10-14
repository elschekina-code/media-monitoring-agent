# Rapport de test — MEDIA MONITORING AGENT (DONNÉES FICTIVES)

> ⚠️ **TEST / SIMULATION.** Toutes les données ci-dessous sont fictives
> (`est_test=oui`). Elles ne constituent pas de véritables reprises et ne sont
> pas comptabilisées comme telles. Date : 2026-10-10.

## Communiqué fictif analysé
- Référence : `CP-TEST-20261010-001`
- Titre : Horizon Software lance Nébulis, sa nouvelle plateforme cloud (FICTIF)
- Émetteur : Horizon Software (société fictive)
- Date : 2026-10-09

## Résultat du dry-run
- Reprises écrites : 4 (toutes `est_test=oui`)
- Doublons détectés et marqués : 1
- Reprises réelles (doit être 0) : 0
- Lignes de journal : 7

## Tableau des reprises (test)
| id | média | pays | type | statut dédup |
|---|---|---|---|---|
| REP-20261010-001 | Presse Tech Afrique | Côte d'Ivoire | reprise_integrale | ok |
| REP-20261010-002 | Échos du Numérique | France | reprise_partielle | ok |
| REP-20261010-003 | Global Tech Review | Royaume-Uni | citation | ok |
| REP-20261010-004 | Presse Tech Afrique | Côte d'Ivoire | syndication | doublon |

## Vérifications
- [x] Schéma des CSV respecté (séparateur `;`, encodage UTF-8)
- [x] Déduplication fonctionnelle (1 doublon marqué, aucune ligne supprimée)
- [x] Traçabilité dans `journal.csv`
- [x] Données de test marquées et exclues des comptages réels
