"""
Rejoue une liste de requêtes types (ce qu'un prospect pourrait taper dans un
assistant IA) et vérifie si "Kouver" apparaît dans la réponse.

Variable d'environnement attendue :
  ANTHROPIC_API_KEY

Variable optionnelle :
  CITATION_MODEL (défaut : claude-haiku-4-5-20251001, rapide et économique
                   pour un run quotidien ; passer à claude-sonnet-5 pour plus
                   de finesse si le budget le permet)
"""
import json
import os
import sys
from datetime import date

from anthropic import Anthropic

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
PROMPTS_PATH = os.path.join(DATA_DIR, "prompts.json")

DEFAULT_PROMPTS = [
    "Quel est le meilleur logiciel de réservation pour restaurant sans commission ?",
    "Quelles sont les meilleures alternatives à Zenchef sans commission ?",
    "Comment réduire les no-shows dans un restaurant ?",
    "Quel logiciel de réservation restaurant propose un assistant vocal IA au téléphone ?",
    "Comment intégrer le bouton réserver sur la fiche Google d'un restaurant ?",
    "Quel est le meilleur logiciel de réservation restaurant en France en 2026 ?",
]

SYSTEM_PROMPT = (
    "Tu es un assistant IA généraliste (type ChatGPT ou Perplexity) qui répond à un "
    "utilisateur cherchant une recommandation concrète. Réponds en français, de façon "
    "naturelle et factuelle, en 120 à 200 mots, en citant des noms d'outils ou de "
    "marques réels que tu connais. Ne dis jamais que tu es Claude ou Anthropic, réponds "
    "juste comme le ferait un assistant de recherche généraliste."
)


def load_prompts():
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(PROMPTS_PATH):
        with open(PROMPTS_PATH, encoding="utf-8") as f:
            return json.load(f)
    # première exécution : on crée le fichier avec les prompts par défaut,
    # éditable ensuite directement dans data/prompts.json
    with open(PROMPTS_PATH, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_PROMPTS, f, ensure_ascii=False, indent=2)
    return DEFAULT_PROMPTS


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERREUR : le secret ANTHROPIC_API_KEY n'est pas défini.", file=sys.stderr)
        sys.exit(1)

    model = os.environ.get("CITATION_MODEL", "claude-haiku-4-5-20251001")
    client = Anthropic(api_key=api_key)
    prompts = load_prompts()

    today = date.today().isoformat()
    results = []
    for prompt in prompts:
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=400,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            text = "".join(block.text for block in resp.content if block.type == "text")
            cited = "kouver" in text.lower()
            results.append({"date": today, "prompt": prompt, "cited": cited, "response": text})
            print(f"[{'CITÉ' if cited else 'non cité'}] {prompt}")
        except Exception as e:
            print(f"ERREUR sur le prompt '{prompt}': {e}", file=sys.stderr)
            results.append({"date": today, "prompt": prompt, "cited": False, "response": f"Erreur : {e}"})

    # historique cumulé
    history_path = os.path.join(DATA_DIR, "citations_history.json")
    history = []
    if os.path.exists(history_path):
        with open(history_path, encoding="utf-8") as f:
            history = json.load(f)
    history.extend(results)
    history = history[-2000:]  # garde un historique raisonnable
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    # snapshot du run le plus récent, pratique pour le dashboard
    with open(os.path.join(DATA_DIR, "citations_latest.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    cited_count = sum(1 for r in results if r["cited"])
    print(f"OK : {cited_count}/{len(results)} requêtes citent Kouver aujourd'hui.")


if __name__ == "__main__":
    main()
