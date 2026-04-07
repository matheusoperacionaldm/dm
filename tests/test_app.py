from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app import create_app


def test_home_page_loads() -> None:
    app = create_app()
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert "Análise automática por link do produto" in response.get_data(as_text=True)


def test_link_analysis_flow(monkeypatch) -> None:
    app = create_app()
    client = app.test_client()

    def fake_analyze_product_url(url: str):
        assert "amazon.com.br" in url
        return {
            "platform": "amazon",
            "title": "Produto X",
            "manufacturer": "Marca X",
            "price": 120.0,
            "sales_count": 240,
            "reviews_count": 87,
            "reviews_quality": "Boas",
            "rating": 4.5,
            "tax_percent": 18.0,
            "lucro_percent": 22.0,
            "price_vs_competitors_percent": -4.5,
            "is_good_to_sell": "Sim",
            "saved_file": "research_history/amazon_20260101_101010.json",
            "improvements": {
                "titulo": "Melhorar com palavra-chave",
                "descricao": "Adicionar diferenciais",
                "fotos": "Mais fotos",
                "capa": "Melhor capa",
                "preco": "Preço competitivo",
            },
            "analyzed_at": "2026-01-01T10:10:10Z",
        }

    monkeypatch.setattr("app.analyze_product_url", fake_analyze_product_url)

    response = client.post("/analisar-link", data={"product_url": "https://www.amazon.com.br/dp/B0TESTE"})

    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Produto X" in body
    assert "Bom para venda?" in body
    assert "Desenvolvido por Matheus Bassini" in body
