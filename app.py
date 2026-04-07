from __future__ import annotations

from dataclasses import asdict

from flask import Flask, render_template, request

from market_research import OpportunityAnalyzer
from market_research.fetchers import fetch_market_data


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def index():
        return render_template("index.html", results=None, error=None)

    @app.post("/analisar")
    def analisar():
        query = (request.form.get("query") or "").strip()
        selected_platforms = request.form.getlist("platforms")
        min_aproveitamento = request.form.get("min_aproveitamento", "8")

        if not query:
            return render_template("index.html", results=None, error="Digite um produto para pesquisar.")
        if not selected_platforms:
            return render_template("index.html", results=None, error="Selecione ao menos uma plataforma.")

        try:
            min_aproveitamento_float = float(min_aproveitamento)
        except ValueError:
            return render_template(
                "index.html",
                results=None,
                error="O valor de aproveitamento mínimo precisa ser numérico.",
            )

        try:
            listings = fetch_market_data(query=query, platforms=selected_platforms)
            if not listings:
                return render_template(
                    "index.html",
                    results=[],
                    error="Nenhum resultado encontrado. Tente outro termo.",
                )
            analyzer = OpportunityAnalyzer(min_aproveitamento_percent=min_aproveitamento_float)
            results = [asdict(item) for item in analyzer.analyze(listings)]
        except Exception as exc:  # noqa: BLE001
            return render_template("index.html", results=None, error=f"Erro ao consultar marketplaces: {exc}")

        return render_template("index.html", results=results, error=None)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
