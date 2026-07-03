"""
Construit un tableau de bord HTML statique (docs/index.html) à partir des
fichiers JSON générés par fetch_gsc_data.py et check_ai_citations.py.
Publié automatiquement par GitHub Pages si Pages pointe sur /docs.
"""
import json
import os
from datetime import date, datetime

BASE = os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.path.join(BASE, "data")
DOCS_DIR = os.path.join(BASE, "docs")


def load_json(name, default):
    path = os.path.join(DATA_DIR, name)
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def main():
    pages = load_json("gsc_pages.json", {"rows": []}).get("rows", [])
    queries = load_json("gsc_queries.json", {"rows": []}).get("rows", [])
    gsc_history = load_json("gsc_history.json", [])
    citations_latest = load_json("citations_latest.json", [])
    citations_history = load_json("citations_history.json", [])
    opportunities = load_json("opportunities.json", [])

    top_pages = sorted(pages, key=lambda r: -r["clicks"])[:15]
    striking = sorted(
        [r for r in queries if 4 <= r["position"] <= 20 and r["impressions"] >= 20],
        key=lambda r: -r["impressions"],
    )[:15]

    cited_today = sum(1 for r in citations_latest if r.get("cited"))
    total_today = len(citations_latest) or 1
    citation_rate = round(100 * cited_today / total_today)

    # taux de citation historique par jour (moyenne)
    by_day = {}
    for r in citations_history:
        by_day.setdefault(r["date"], []).append(r["cited"])
    trend = sorted(by_day.items())[-30:]
    trend_rows = "".join(
        f'<div class="trend-row"><span>{d}</span>'
        f'<div class="bar-track"><div class="bar-fill" style="width:{round(100*sum(v)/len(v))}%"></div></div>'
        f'<span>{round(100*sum(v)/len(v))}%</span></div>'
        for d, v in trend
    )
    no_history_msg = '<p class="empty">Pas encore assez d\u2019historique.</p>'
    trend_html = trend_rows if trend_rows else no_history_msg

    pages_rows = "".join(
        f'<div class="row-card"><span class="lbl">{esc(r["label"])}</span>'
        f'<span class="mono">{r["clicks"]} clics · {r["impressions"]} impr. · pos. {r["position"]}</span></div>'
        for r in top_pages
    ) or '<p class="empty">Pas encore de données — attends le premier run programmé.</p>'

    striking_rows = "".join(
        f'<div class="row-card"><span class="lbl">{esc(r["label"])}</span>'
        f'<span class="mono">pos. {r["position"]} · {r["impressions"]} impr. · CTR {r["ctr"]}%</span></div>'
        for r in striking
    ) or '<p class="empty">Aucune opportunité "striking distance" détectée pour le moment.</p>'

    citations_rows = "".join(
        f'<div class="ticket {"cited" if r.get("cited") else "notcited"}">'
        f'<div class="ticket-top"><strong>{esc(r["prompt"])}</strong>'
        f'<span class="stamp {"cited" if r.get("cited") else "notcited"}">{"Cité ✓" if r.get("cited") else "Non cité ✗"}</span></div>'
        f'</div>'
        for r in citations_latest
    ) or '<p class="empty">Pas encore de test de citation exécuté.</p>'

    opp_rows = "".join(
        f'<div class="row-card-static"><strong>{esc(o["topic"])}</strong><p>{esc(o["why"])}</p></div>'
        for o in opportunities
    )

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Kouver — Radar GEO/SEO</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body{{margin:0;background:#F3EDE0;color:#2B211A;font-family:-apple-system,Segoe UI,Arial,sans-serif;}}
  .wrap{{max-width:860px;margin:0 auto;padding:40px 24px 80px;}}
  h1{{font-size:26px;margin-bottom:4px;}}
  .updated{{font-size:12px;color:#6B5F51;margin-bottom:32px;}}
  h2{{font-size:17px;margin:36px 0 12px;border-bottom:1px solid rgba(43,33,26,0.12);padding-bottom:6px;}}
  .stat-strip{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:8px;}}
  .stat{{background:#1F1712;color:#F3EDE0;border-radius:10px;padding:14px 18px;flex:1;min-width:130px;}}
  .stat .num{{font-size:22px;font-weight:700;color:#B98B3E;}}
  .stat .lbl{{font-size:10px;letter-spacing:.6px;text-transform:uppercase;opacity:.7;}}
  .row-card{{display:flex;justify-content:space-between;gap:10px;background:#fff;border-radius:8px;padding:10px 14px;margin-bottom:6px;font-size:13px;}}
  .row-card-static{{background:#fff;border-radius:8px;padding:12px 14px;margin-bottom:8px;}}
  .row-card-static p{{font-size:12.5px;color:#6B5F51;margin:4px 0 0;}}
  .mono{{font-family:monospace;white-space:nowrap;color:#6B5F51;font-size:12px;}}
  .ticket{{background:#fff;border-left:3px solid #7A2231;border-radius:2px;padding:10px 14px;margin-bottom:6px;}}
  .ticket.cited{{border-left-color:#4B6353;}}
  .ticket-top{{display:flex;justify-content:space-between;gap:10px;font-size:13px;align-items:center;}}
  .stamp{{font-size:10px;font-weight:700;padding:3px 8px;border-radius:20px;white-space:nowrap;}}
  .stamp.cited{{background:rgba(75,99,83,0.15);color:#4B6353;}}
  .stamp.notcited{{background:rgba(122,34,49,0.1);color:#7A2231;}}
  .trend-row{{display:flex;align-items:center;gap:10px;font-size:11px;color:#6B5F51;margin-bottom:4px;}}
  .trend-row span:first-child{{width:80px;}}
  .trend-row span:last-child{{width:36px;text-align:right;}}
  .bar-track{{flex:1;background:#E9E0CC;border-radius:3px;height:6px;overflow:hidden;}}
  .bar-fill{{background:#7A2231;height:100%;}}
  .empty{{font-size:12.5px;color:#6B5F51;font-style:italic;}}
  a{{color:#7A2231;}}
</style>
</head>
<body>
<div class="wrap">
  <h1>Kouver — Radar GEO/SEO</h1>
  <div class="updated">Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M')} · généré automatiquement</div>

  <div class="stat-strip">
    <div class="stat"><div class="num">{cited_today}/{len(citations_latest)}</div><div class="lbl">Citations aujourd'hui</div></div>
    <div class="stat"><div class="num">{citation_rate}%</div><div class="lbl">Taux de citation</div></div>
    <div class="stat"><div class="num">{len(pages)}</div><div class="lbl">Pages suivies (GSC)</div></div>
    <div class="stat"><div class="num">{len(striking)}</div><div class="lbl">Opportunités striking distance</div></div>
  </div>

  <h2>Tendance du taux de citation IA (30 derniers runs)</h2>
  {trend_html}

  <h2>Dernier test de citations</h2>
  {citations_rows}

  <h2>Top pages par clics (Search Console, 28 derniers jours)</h2>
  {pages_rows}

  <h2>Opportunités "striking distance" (position 4-20)</h2>
  {striking_rows}

  <h2>Idées de contenu à explorer</h2>
  {opp_rows}
</div>
</body>
</html>"""

    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print("OK : docs/index.html généré.")


if __name__ == "__main__":
    main()
