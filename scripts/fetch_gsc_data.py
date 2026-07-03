"""
Récupère les statistiques de performance (clics, impressions, position) depuis
Google Search Console pour le site Kouver, et les enregistre en JSON.

Variables d'environnement attendues :
  GSC_SERVICE_ACCOUNT_JSON : contenu complet du fichier JSON de la clé du compte de service
  GSC_SITE_URL              : propriété Search Console, ex "https://www.kouver.fr/"
                               ou "sc-domain:kouver.fr" pour une propriété de type domaine
"""
import json
import os
import sys
from datetime import date, timedelta

from google.oauth2 import service_account
from googleapiclient.discovery import build

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]


def get_credentials():
    raw = os.environ.get("GSC_SERVICE_ACCOUNT_JSON")
    if not raw:
        print("ERREUR : le secret GSC_SERVICE_ACCOUNT_JSON n'est pas défini.", file=sys.stderr)
        sys.exit(1)
    try:
        info = json.loads(raw)
    except json.JSONDecodeError:
        print("ERREUR : GSC_SERVICE_ACCOUNT_JSON n'est pas un JSON valide.", file=sys.stderr)
        sys.exit(1)
    return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)


def query_search_console(service, site_url, dimensions, start_date, end_date, row_limit=1000):
    body = {
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "dimensions": dimensions,
        "rowLimit": row_limit,
    }
    response = service.searchanalytics().query(siteUrl=site_url, body=body).execute()
    rows = response.get("rows", [])
    out = []
    for r in rows:
        out.append({
            "label": r["keys"][0],
            "clicks": r.get("clicks", 0),
            "impressions": r.get("impressions", 0),
            "ctr": round(r.get("ctr", 0) * 100, 2),
            "position": round(r.get("position", 0), 1),
        })
    return out


def main():
    site_url = os.environ.get("GSC_SITE_URL")
    if not site_url:
        print("ERREUR : la variable de repo GSC_SITE_URL n'est pas définie.", file=sys.stderr)
        sys.exit(1)

    creds = get_credentials()
    service = build("searchconsole", "v1", credentials=creds)

    end_date = date.today() - timedelta(days=3)   # GSC a ~2-3 jours de délai
    start_date = end_date - timedelta(days=28)

    os.makedirs(DATA_DIR, exist_ok=True)

    try:
        pages = query_search_console(service, site_url, ["page"], start_date, end_date)
        queries = query_search_console(service, site_url, ["query"], start_date, end_date)
    except Exception as e:
        print(f"ERREUR lors de l'appel à l'API Search Console : {e}", file=sys.stderr)
        print("Vérifie que le compte de service a bien été ajouté comme utilisateur "
              "dans Search Console (Paramètres > Utilisateurs et autorisations).", file=sys.stderr)
        sys.exit(1)

    with open(os.path.join(DATA_DIR, "gsc_pages.json"), "w", encoding="utf-8") as f:
        json.dump({"generated_at": date.today().isoformat(), "period": [start_date.isoformat(), end_date.isoformat()], "rows": pages}, f, ensure_ascii=False, indent=2)

    with open(os.path.join(DATA_DIR, "gsc_queries.json"), "w", encoding="utf-8") as f:
        json.dump({"generated_at": date.today().isoformat(), "period": [start_date.isoformat(), end_date.isoformat()], "rows": queries}, f, ensure_ascii=False, indent=2)

    # historique cumulé (pour suivre la tendance clics/impressions dans le temps)
    history_path = os.path.join(DATA_DIR, "gsc_history.json")
    history = []
    if os.path.exists(history_path):
        with open(history_path, encoding="utf-8") as f:
            history = json.load(f)
    history.append({
        "date": date.today().isoformat(),
        "total_clicks": sum(p["clicks"] for p in pages),
        "total_impressions": sum(p["impressions"] for p in pages),
        "pages_count": len(pages),
        "queries_count": len(queries),
    })
    history = history[-180:]  # garde ~6 mois d'historique
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    print(f"OK : {len(pages)} pages et {len(queries)} requêtes récupérées "
          f"({start_date} → {end_date}).")


if __name__ == "__main__":
    main()
