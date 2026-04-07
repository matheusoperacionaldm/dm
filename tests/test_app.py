from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app import create_app
from market_research.models import ProductListing


def test_home_page_loads() -> None:
    app = create_app()
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert "Pesquisa automática de produtos" in response.get_data(as_text=True)


def test_search_and_analyze(monkeypatch) -> None:
    app = create_app()
    client = app.test_client()

    def fake_fetch_market_data(query: str, platforms: list[str]):
        assert query == "fone bluetooth"
        assert "amazon" in platforms
        return [
            ProductListing(
                platform="amazon",
                product_name="Fone Bluetooth X",
                category="eletronicos",
                seller="seller1",
                unit_price_brl=100,
                units_sold_last_30d=300,
                shipping_cost_brl=8,
                product_cost_brl=50,
                ad_cost_brl=5,
                marketplace_fee_percent=18,
            )
        ]

    monkeypatch.setattr("app.fetch_market_data", fake_fetch_market_data)

    response = client.post(
        "/analisar",
        data={
            "query": "fone bluetooth",
            "platforms": ["amazon"],
            "min_aproveitamento": "8",
        },
    )

    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Fone Bluetooth X" in body
    assert "Vale a pena" in body
    assert "Impostos/Taxas (%)" in body
