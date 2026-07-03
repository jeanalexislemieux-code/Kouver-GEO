# Kouver — Radar GEO/SEO automatisé

Ce repo fait tourner, **chaque jour et gratuitement**, un rapport qui :

1. récupère tes vraies statistiques Search Console (clics, impressions, position par page et par requête) ;
2. teste une liste de requêtes types pour voir si Kouver est cité par une IA généraliste ;
3. publie un tableau de bord HTML à jour sur GitHub Pages.

Tout tourne via **GitHub Actions** (gratuit) sur un planning quotidien. Coût réel : quelques centimes par mois d'API Anthropic (le modèle utilisé par défaut, Haiku, est le moins cher de la gamme). Google Search Console est gratuit.

---

## Étape 1 — Créer l'accès à l'API Search Console (≈10 min, une seule fois)

1. Va sur [console.cloud.google.com](https://console.cloud.google.com) et crée un projet (gratuit, pas de carte requise pour ça).
2. Dans le menu, va sur **API et services > Bibliothèque**, cherche **"Search Console API"**, clique **Activer**.
3. Va sur **API et services > Identifiants > Créer des identifiants > Compte de service**.
   - Donne-lui un nom (ex : `kouver-geo-bot`), pas besoin de rôle particulier au niveau du projet.
4. Une fois le compte de service créé, ouvre-le, va dans l'onglet **Clés > Ajouter une clé > Créer une clé > JSON**.
   - Un fichier `.json` se télécharge. **Garde-le précieusement, ne le commite jamais dans le repo.**
5. Note l'adresse e-mail du compte de service (ressemble à `kouver-geo-bot@ton-projet.iam.gserviceaccount.com`).

## Étape 2 — Autoriser ce compte dans Search Console (≈2 min)

1. Va sur [search.google.com/search-console](https://search.google.com/search-console), sélectionne la propriété **kouver.fr**.
2. **Paramètres > Utilisateurs et autorisations > Ajouter un utilisateur**.
3. Colle l'e-mail du compte de service (étape 1.5), autorisation **"Complet"** (ou "Restreint" si tu veux juste de la lecture — Restreint suffit ici, ce script ne fait que lire).

## Étape 3 — Créer le repo GitHub

1. Crée un nouveau repo sur GitHub (public ou privé — privé fonctionne aussi, Actions a un quota gratuit mensuel).
2. Pousse tous les fichiers de ce dossier dedans (`git init`, `git add .`, `git commit`, `git push`, ou glisser-déposer via l'interface web GitHub si tu préfères).

## Étape 4 — Ajouter les secrets et la variable

Dans le repo GitHub : **Settings > Secrets and variables > Actions**.

**Onglet "Secrets" → New repository secret :**
- `ANTHROPIC_API_KEY` : ta clé API, créée sur [console.anthropic.com](https://console.anthropic.com) (Settings > API Keys).
- `GSC_SERVICE_ACCOUNT_JSON` : ouvre le fichier `.json` téléchargé à l'étape 1, colle **tout son contenu** tel quel.

**Onglet "Variables" → New repository variable :**
- `GSC_SITE_URL` : l'identifiant exact de ta propriété Search Console. Deux formats possibles selon comment kouver.fr est enregistré dans GSC :
  - Propriété de type "Préfixe d'URL" → `https://www.kouver.fr/` (avec le slash final)
  - Propriété de type "Domaine" → `sc-domain:kouver.fr`
  - Tu peux voir le format exact en haut à gauche de Search Console, à côté du sélecteur de propriété.

## Étape 5 — Activer GitHub Pages

**Settings > Pages** :
- Source : **Deploy from a branch**
- Branch : **main**, dossier **`/docs`**
- Sauvegarde. Après le premier run, ton tableau de bord sera visible à `https://TON-COMPTE.github.io/TON-REPO/`.

## Étape 6 — Premier lancement manuel

**Onglet Actions > "Rapport GEO/SEO quotidien" > Run workflow.**

Regarde les logs : s'il y a une erreur d'authentification Search Console, la cause la plus fréquente est un oubli à l'étape 2 (compte de service pas ajouté comme utilisateur) ou un `GSC_SITE_URL` mal formaté.

Une fois que ça tourne, le workflow se relance **automatiquement chaque jour à 6h UTC**, sans rien faire de plus.

---

## Structure du repo

```
.github/workflows/daily-report.yml   → planning + orchestration
scripts/fetch_gsc_data.py            → appelle l'API Search Console
scripts/check_ai_citations.py        → teste les citations IA via l'API Anthropic
scripts/build_dashboard.py           → génère docs/index.html
data/prompts.json                    → requêtes testées pour les citations (créé au 1er run, éditable)
data/opportunities.json              → idées de contenu (éditable directement)
data/*.json                          → données brutes + historique, mis à jour à chaque run
docs/index.html                      → le tableau de bord publié par GitHub Pages
```

## Pour aller plus loin

- **Changer le planning** : modifie la ligne `cron` dans `.github/workflows/daily-report.yml` ([aide-mémoire cron](https://crontab.guru)).
- **Ajouter/retirer des requêtes de citation** : édite `data/prompts.json` directement (créé après le premier run).
- **Passer à un modèle plus fin pour les citations** : ajoute une variable de repo `CITATION_MODEL` avec la valeur `claude-sonnet-5` (plus cher, plus nuancé que Haiku).
- **Notifications** : si tu veux être alerté par email/Slack en cas de nouvelle citation, ajoute une étape au workflow — dis-le-moi si tu veux que je la construise.
