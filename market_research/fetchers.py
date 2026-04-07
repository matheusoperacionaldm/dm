from __future__ import annotations

import re
from typing import Iterable
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from .models import ProductListing

DEFAULT_TIMEOUT = 20
PLATFORM_TAX_PERCENT = {
    "mercado livre": 16.0,
    "amazon": 18.0,
    "shopee": 14.0,
}


class FetchError(RuntimeError):
    """Falha ao coletar dados de marketplaces."""


def fetch_market_data(
    query: str,
    platforms: Iterable[str],
    limit: int = 20,
    product_cost_percent: float = 55.0,
    shipping_percent: float = 8.0,
    ad_percent: float = 5.0,
) -> list[ProductListing]:
    """Busca produtos automaticamente sem CSV."""

    listings: list[ProductListing] = []
    for platform in platforms:
        normalized = platform.strip().lower()
        if normalized == "mercado livre":
            listings.extend(
                _fetch_mercado_livre(
                    query,
                    limit=limit,
                    product_cost_percent=product_cost_percent,
                    shipping_percent=shipping_percent,
                    ad_percent=ad_percent,
                )
            )
        elif normalized == "amazon":
            listings.extend(
                _fetch_amazon(
                    query,
                    limit=limit,
                    product_cost_percent=product_cost_percent,
                    shipping_percent=shipping_percent,
                    ad_percent=ad_percent,
                )
            )
        elif normalized == "shopee":
            listings.extend(
                _fetch_shopee(
                    query,
                    limit=limit,
                    product_cost_percent=product_cost_percent,
                    shipping_percent=shipping_percent,
                    ad_percent=ad_percent,
                )
            )
    return listings


def _fetch_mercado_livre(
    query: str,
    limit: int,
    product_cost_percent: float,
    shipping_percent: float,
    ad_percent: float,
) -> list[ProductListing]:
    url = f"https://api.mercadolibre.com/sites/MLB/search?q={quote_plus(query)}&limit={limit}"
    response = requests.get(url, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    data = response.json()

    listings: list[ProductListing] = []
    for item in data.get("results", []):
        price = float(item.get("price") or 0)
        sold = int(item.get("sold_quantity") or 0)
        title = item.get("title") or query
        category = str(item.get("category_id") or "geral")
        listings.append(
            _build_listing(
                platform="mercado livre",
                product_name=title,
                category=category,
                seller=str(item.get("seller", {}).get("id", "desconhecido")),
                unit_price_brl=price,
                units_sold_last_30d=sold,
                product_cost_percent=product_cost_percent,
                shipping_percent=shipping_percent,
                ad_percent=ad_percent,
            )
        )
    return listings


def _fetch_amazon(
    query: str,
    limit: int,
    product_cost_percent: float,
    shipping_percent: float,
    ad_percent: float,
) -> list[ProductListing]:
    url = f"https://www.amazon.com.br/s?k={quote_plus(query)}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    cards = soup.select("div.s-result-item[data-asin]")[:limit]

    listings: list[ProductListing] = []
    for card in cards:
        title_tag = card.select_one("h2 span")
        whole = card.select_one("span.a-price-whole")
        frac = card.select_one("span.a-price-fraction")
        if not title_tag or not whole:
            continue

        title = title_tag.get_text(strip=True)
        price = _parse_price_br(whole.get_text(strip=True), frac.get_text(strip=True) if frac else "00")
        sold = _extract_sold_count(card.get_text(" ", strip=True))
        if price <= 0:
            continue

        listings.append(
            _build_listing(
                platform="amazon",
                product_name=title,
                category="geral",
                seller="amazon-market",
                unit_price_brl=price,
                units_sold_last_30d=sold,
                product_cost_percent=product_cost_percent,
                shipping_percent=shipping_percent,
                ad_percent=ad_percent,
            )
        )
    return listings


def _fetch_shopee(
    query: str,
    limit: int,
    product_cost_percent: float,
    shipping_percent: float,
    ad_percent: float,
) -> list[ProductListing]:
    url = (
        "https://shopee.com.br/api/v4/search/search_items"
        f"?by=relevancy&keyword={quote_plus(query)}&limit={limit}&newest=0&order=desc&page_type=search"
    )
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://shopee.com.br/"}
    response = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    data = response.json()

    listings: list[ProductListing] = []
    for wrapper in data.get("items", []):
        item = wrapper.get("item_basic", {})
        price_min = float(item.get("price_min") or 0) / 100000
        sold = int(item.get("historical_sold") or 0)
        title = item.get("name") or query
        if price_min <= 0:
            continue

        listings.append(
            _build_listing(
                platform="shopee",
                product_name=title,
                category=str(item.get("catid") or "geral"),
                seller=str(item.get("shopid") or "desconhecido"),
                unit_price_brl=price_min,
                units_sold_last_30d=sold,
                product_cost_percent=product_cost_percent,
                shipping_percent=shipping_percent,
                ad_percent=ad_percent,
            )
        )
    return listings


def _build_listing(
    platform: str,
    product_name: str,
    category: str,
    seller: str,
    unit_price_brl: float,
    units_sold_last_30d: int,
    product_cost_percent: float,
    shipping_percent: float,
    ad_percent: float,
) -> ProductListing:
    return ProductListing(
        platform=platform,
        product_name=product_name,
        category=category,
        seller=seller,
        unit_price_brl=unit_price_brl,
        units_sold_last_30d=units_sold_last_30d,
        shipping_cost_brl=unit_price_brl * (shipping_percent / 100),
        product_cost_brl=unit_price_brl * (product_cost_percent / 100),
        ad_cost_brl=unit_price_brl * (ad_percent / 100),
        marketplace_fee_percent=PLATFORM_TAX_PERCENT[platform],
    )


def _parse_price_br(whole: str, fraction: str) -> float:
    normalized_whole = whole.replace(".", "").replace(",", "")
    normalized_fraction = re.sub(r"\D", "", fraction) or "00"
    return float(f"{int(normalized_whole)}.{normalized_fraction[:2]:0<2}")


def _extract_sold_count(text: str) -> int:
    patterns = [
        r"(\d+[\d\.]*)\+?\s*comprados",
        r"(\d+[\d\.]*)\+?\s*vendas",
        r"mais de\s*(\d+[\d\.]*)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return int(match.group(1).replace(".", ""))
    return 0
