from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import market_research.link_analysis as la


class DummyResponse:
    def __init__(self, text: str, ok: bool = True):
        self.text = text
        self.ok = ok

    def raise_for_status(self):
        return None


def test_analyze_amazon_without_title_does_not_crash(monkeypatch) -> None:
    product_html = "<html><body><span class='a-price-whole'>123</span><span class='a-price-fraction'>45</span></body></html>"
    search_html = "<html><body></body></html>"

    calls = {"n": 0}

    def fake_get(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            return DummyResponse(product_html)
        return DummyResponse(search_html)

    monkeypatch.setattr(la.requests, "get", fake_get)

    result = la._analyze_amazon("https://www.amazon.com.br/dp/B0TESTE")

    assert result["title"] == "Sem título"
    assert result["price"] == 123.45
