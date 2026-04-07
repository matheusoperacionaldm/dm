from __future__ import annotations

import io
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app import create_app


def test_home_page_loads() -> None:
    app = create_app()
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert "Sistema Local de Pesquisa de Mercado" in response.get_data(as_text=True)


def test_upload_and_analyze_csv() -> None:
    app = create_app()
    client = app.test_client()

    csv_content = """platform,product_name,category,seller,unit_price_brl,units_sold_last_30d,shipping_cost_brl,product_cost_brl,ad_cost_brl,marketplace_fee_percent
mercado livre,Fone Bluetooth TWS,eletronicos,loja_a,129.9,430,12.0,58.0,5.0,16.0
amazon,Fone Bluetooth TWS,eletronicos,loja_b,139.9,280,10.0,60.0,7.0,17.0
shopee,Fone Bluetooth TWS,eletronicos,loja_c,119.9,520,13.0,56.0,4.5,14.0
"""
    data = {
        "min_aproveitamento": "8",
        "csv_file": (io.BytesIO(csv_content.encode("utf-8")), "dados.csv"),
    }

    response = client.post("/analisar", data=data, content_type="multipart/form-data")

    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Fone Bluetooth TWS" in body
    assert "Vale a pena" in body
