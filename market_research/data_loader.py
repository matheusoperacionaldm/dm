from __future__ import annotations

import csv
from pathlib import Path

from .models import ProductListing


REQUIRED_COLUMNS = {
    "platform",
    "product_name",
    "category",
    "seller",
    "unit_price_brl",
    "units_sold_last_30d",
    "shipping_cost_brl",
    "product_cost_brl",
    "ad_cost_brl",
    "marketplace_fee_percent",
}


def load_listings_from_csv(csv_path: Path) -> list[ProductListing]:
    """Carrega anúncios a partir de um CSV local."""

    with csv_path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames:
            raise ValueError("CSV sem cabeçalho.")

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
