# SECURITE.md — Inventaire documentaire des permissions et accès

> Document de sécurité établi en **lecture seule**. Aucune valeur secrète (jeton, mot de passe, clé, identifiant de ressource) n'est reproduite dans ce document.

## Objet

Inventorier les artefacts d'accès présents dans l'environnement, leurs **permissions déclarées**, les risques associés et les recommandations de remédiation. Ce document sert de référence pour les correctifs C1/C2/C3 du plan de sécurisation.

---

## 1. Inventaire des artefacts d'accès (noms et scopes uniquement — jamais les valeurs)

| Artefact | Emplacement | Type | Permissions / scope déclarés |
|---|---|---|---|
| `gmail_token.enc` | `%LOCALAPPDATA%\AdminOpsAI\` | Jeton OAuth Google (chiffré DPAPI) | `gmail.readonly` (lecture seule Gmail) + `drive.file` (fichiers Drive créés par l'application) |
| `cvlynk_agent.enc` | `%LOCALAPPDATA%\AdminOpsAI\` | Jeton d'agent orchestrateur CVlynk (chiffré DPAPI) | Identité d'agent auprès de l'orchestrateur (heartbeat, consultation/acquittement de tâches) |
| `sheet_id.json` | `%LOCALAPPDATA%\AdminOpsAI\` | Identifiant de feuille Google | Cible d'export Sheets (couvert par `drive.file`) |
| Passerelle Telegram | Configuration Hermes | Filtre d'autorisation | Restreinte à un identifiant utilisateur unique autorisé |

**Précision importante** : ces artefacts appartiennent au projet **AdminOps AI**. Le projet **Media Monitoring Agent ne détient aucun jeton, aucune clé ni aucun compte propre** — accès minimal par conception.

> Note de méthode : les scopes ci-dessus sont **déclarés** (configuration connue de l'environnement). Ils n'ont pas été relus dans les fichiers chiffrés, conformément à la règle « ne jamais lire/déchiffrer les valeurs ».

---

## 2. Périmètre d'accès du Media Monitoring Agent

| Capacité | Portée |
|---|---|
| `web_search` / `web_extract` | Recherche et extraction web publiques (lecture) |
| `browser_exec` | Navigateur complet (⚠️ inclut l'accès au coffre de mots de passe) |
| Système de fichiers | Lecture/écriture **limitée à `media-monitoring-agent/`** |
| AdminOps AI | **Aucun accès déclaré** — séparation par convention de fichiers |

---

## 3. Risques identifiés (synthèse de l'audit)

| Réf. | Risque | Gravité |
|---|---|---|
| A1 | `browser_exec` inclut le coffre de mots de passe et des sessions navigateur potentiellement connectées | Élevée |
| A2 | DPAPI = déchiffrable par tout processus du **même utilisateur Windows** → isolation inter-projets logique, non technique | Élevée |
| A3 | `gmail.readonly` + `drive.file` + API Sheets = lecture Gmail + écriture sur la feuille partagée | Moyenne |
| V1 | Injection d'instructions via le contenu des pages web extraites | Élevée |
| V3 | Absence de contrôle de version du projet médias | Moyenne |
| V4 | Séparation test/réel par simple indicateur `est_test` | Moyenne |
| V5 | Dépendances Python non épinglées | Faible |

---

## 4. Recommandations (à exécuter sur validation — correctifs C1/C2/C3…)

| Correctif | Description | Exécuteur |
|---|---|---|
| **C1** | Session navigateur **dédiée et isolée** (`session="media-monitoring"`) | Agent (sur accord) |
| **C2** | Interdiction procédurale du coffre de mots de passe ; désactivation réelle du coffre = option config Hermes (accord explicite requis) | Agent + vous |
| **C3** | Isolation Windows effective : **compte Windows dédié** pour AdminOps AI (recommandé) ou Windows Credential Manager | Vous / admin |
| — | Réduction éventuelle des scopes OAuth (re-autorisation Google Cloud) | Vous |
| **C6** | `.gitignore` excluant `*.enc`, `*.key`, `*.pem`, `.env`, `credentials*.json` | Agent (sur accord) |

---

## 5. Règles de confidentialité (immuables)

1. Ne jamais **afficher**, **lire** ni **déchiffrer** les valeurs des jetons, mots de passe ou clés.
2. Ne jamais reproduire un identifiant de ressource (feuille, agent, utilisateur) dans un document partagé.
3. Toute modification des permissions (scopes, comptes, coffre) exige une **validation humaine préalable**.
4. Ne jamais désactiver AdminOps AI ni modifier ses fichiers ou paramètres.

---

*Document créé le 10/10/2026 dans le cadre du correctif C4. Aucun fichier ni paramètre d'AdminOps AI ni de configuration globale Hermes n'a été modifié.*
