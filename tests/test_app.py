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
    assert "Alternar tema escuro/claro" in response.get_data(as_text=True)


def test_link_analysis_flow(monkeypatch) -> None:
    app = create_app()
    client = app.test_client()

    def fake_analyze_product_url(url: str):
        return {
            "platform": "amazon",
            "title": "Produto X",
            "manufacturer": "Marca X",
            "sales_last_30d": 700,
            "sales_count": 700,
            "reviews_count": 87,
            "reviews_quality": "Boas",
            "rating": 4.6,
            "tax_percent": 18.0,
            "lucro_percent": 22.0,
            "price_stats": {
                "avg_price": 120.0,
                "min_price": 99.0,
                "min_price_sales": 41,
                "max_price": 170.0,
                "max_price_sales": 20,
            },
            "price_vs_competitors_percent": -3.2,
            "is_good_to_sell": "Bom para vender",
            "saved_file": "research_history/amazon_20260101_101010.json",
            "saved_file_name": "amazon_20260101_101010.json",
            "improvements": {
                "titulo": "Melhorar título",
                "descricao": "Melhorar descrição",
                "fotos": "Melhorar fotos",
                "capa": "Melhorar capa",
                "preco": "Preço competitivo",
                "avaliacoes": "Subir volume de avaliações",
            },
            "analyzed_at": "2026-01-01T10:10:10Z",
        }

    monkeypatch.setattr("app.analyze_product_url", fake_analyze_product_url)
    response = client.post("/analisar-link", data={"product_url": "https://www.amazon.com.br/dp/B0TESTE"})
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Número de vendas nos últimos 30 dias" in body
    assert "Bom para vender" in body
    assert "Nome do arquivo" in body


def test_clear_history(monkeypatch) -> None:
    app = create_app()
    client = app.test_client()

    monkeypatch.setattr("app.clear_history", lambda: 4)
    response = client.post("/limpar-pesquisas")

    assert response.status_code == 200
    assert "Arquivos removidos: 4" in response.get_data(as_text=True)
