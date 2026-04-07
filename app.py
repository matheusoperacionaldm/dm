from __future__ import annotations

import csv
import io
from dataclasses import asdict

from flask import Flask, render_template, request

from market_research import OpportunityAnalyzer
from market_research.data_loader import REQUIRED_COLUMNS
from market_research.models import ProductListing


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def index():
        return render_template("index.html", results=None, error=None)

    @app.post("/analisar")
    def analisar():
        uploaded = request.files.get("csv_file")
        min_aproveitamento = request.form.get("min_aproveitamento", "8")

        if not uploaded or uploaded.filename == "":
            return render_template(
                "index.html",
                results=None,
                error="Envie um arquivo CSV para análise.",
            )

        try:
            min_aproveitamento_float = float(min_aproveitamento)
        except ValueError:
            return render_template(
                "index.html",
                results=None,
                error="O valor de aproveitamento mínimo precisa ser numérico.",
            )

        try:
            listings = _load_listings_from_uploaded_csv(uploaded.read().decode("utf-8"))
            analyzer = OpportunityAnalyzer(min_aproveitamento_percent=min_aproveitamento_float)
            results = [asdict(item) for item in analyzer.analyze(listings)]
        except Exception as exc:  # noqa: BLE001
            return render_template("index.html", results=None, error=f"Erro ao processar CSV: {exc}")

        return render_template("index.html", results=results, error=None)

    return app


def _load_listings_from_uploaded_csv(content: str) -> list[ProductListing]:
    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        raise ValueError("CSV sem cabeçalho")

    missing = REQUIRED_COLUMNS - set(reader.fieldnames)
    if missing:
        missing_fields = ", ".join(sorted(missing))
        raise ValueError(f"CSV inválido, faltam colunas: {missing_fields}")

    listings: list[ProductListing] = []
    for line_number, row in enumerate(reader, start=2):
        try:
            listings.append(
                ProductListing(
                    platform=row["platform"].strip().lower(),
                    product_name=row["product_name"].strip(),
                    category=row["category"].strip(),
                    seller=row["seller"].strip(),
                    unit_price_brl=float(row["unit_price_brl"]),
                    units_sold_last_30d=int(row["units_sold_last_30d"]),
                    shipping_cost_brl=float(row["shipping_cost_brl"]),
                    product_cost_brl=float(row["product_cost_brl"]),
                    ad_cost_brl=float(row["ad_cost_brl"]),
                    marketplace_fee_percent=float(row["marketplace_fee_percent"]),
                )
            )
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"Erro na linha {line_number}: {exc}") from exc

    return listings


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
