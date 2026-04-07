from __future__ import annotations

import json
from pathlib import Path

from flask import Flask, render_template, request

from market_research.link_analysis import HISTORY_DIR, analyze_product_url


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def index():
        return render_template("index.html", result=None, error=None, history=_load_history())

    @app.post("/analisar-link")
    def analisar_link():
        url = (request.form.get("product_url") or "").strip()
        if not url:
            return render_template("index.html", result=None, error="Informe o link do produto.", history=_load_history())

        try:
            result = analyze_product_url(url)
        except Exception as exc:  # noqa: BLE001
            return render_template(
                "index.html",
                result=None,
                error=f"Falha na análise automática: {exc}",
                history=_load_history(),
            )

        return render_template("index.html", result=result, error=None, history=_load_history())

    return app


def _load_history(limit: int = 10) -> list[dict]:
    if not HISTORY_DIR.exists():
        return []
    files = sorted(HISTORY_DIR.glob("*.json"), reverse=True)[:limit]
    items: list[dict] = []
    for file in files:
        try:
            items.append(json.loads(file.read_text(encoding="utf-8")))
        except Exception:  # noqa: BLE001
            continue
    return items


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
