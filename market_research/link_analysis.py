from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from statistics import median
from urllib.parse import quote_plus, urlparse

import requests
from bs4 import BeautifulSoup

DEFAULT_TIMEOUT = 20
HISTORY_DIR = Path("research_history")
USER_AGENT = {"User-Agent": "Mozilla/5.0"}
PLATFORM_TAX = {"mercado livre": 16.0, "amazon": 18.0, "shopee": 14.0}


def analyze_product_url(url: str, product_cost_percent: float = 55.0, ad_percent: float = 5.0) -> dict:
    platform = detect_platform(url)
    if platform == "mercado livre":
        data = _analyze_mercado_livre(url)
    elif platform == "amazon":
        data = _analyze_amazon(url)
    elif platform == "shopee":
        data = _analyze_shopee(url)
    else:
        raise ValueError("Link não suportado. Use Amazon, Shopee ou Mercado Livre.")

    price = float(data.get("price") or 0)
    tax_percent = PLATFORM_TAX[platform]
    cost_value = price * (product_cost_percent / 100)
    ad_value = price * (ad_percent / 100)
    tax_value = price * (tax_percent / 100)
    lucro_value = price - cost_value - ad_value - tax_value
    lucro_percent = (lucro_value / price * 100) if price > 0 else 0.0

    data.update(
        {
            "platform": platform,
            "lucro_percent": round(lucro_percent, 2),
            "tax_percent": round(tax_percent, 2),
            "is_good_to_sell": _is_good_to_sell(data, lucro_percent),
            "improvements": _build_improvement_tips(data),
            "analyzed_at": datetime.utcnow().isoformat() + "Z",
        }
    )
    data["saved_file"] = str(save_analysis(data))
    return data


def detect_platform(url: str) -> str:
    host = (urlparse(url).netloc or "").lower()
    if "mercadolivre" in host or "mercadolibre" in host:
        return "mercado livre"
    if "amazon." in host:
        return "amazon"
    if "shopee." in host:
        return "shopee"
    return "unknown"


def save_analysis(data: dict) -> Path:
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    safe_platform = data.get("platform", "unknown").replace(" ", "_")
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    file_path = HISTORY_DIR / f"{safe_platform}_{stamp}.json"
    file_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return file_path


def _analyze_mercado_livre(url: str) -> dict:
    item_id_match = re.search(r"(MLB-?\d+)", url.upper())
    if not item_id_match:
        raise ValueError("Não foi possível identificar o item do Mercado Livre no link.")
    item_id = item_id_match.group(1).replace("-", "")

    item_resp = requests.get(f"https://api.mercadolibre.com/items/{item_id}", timeout=DEFAULT_TIMEOUT)
    item_resp.raise_for_status()
    item = item_resp.json()

    review_resp = requests.get(f"https://api.mercadolibre.com/reviews/item/{item_id}", timeout=DEFAULT_TIMEOUT)
    rating_avg = 0.0
    reviews_count = 0
    if review_resp.ok:
        review_data = review_resp.json()
        rating_avg = float(review_data.get("rating_average") or 0)
        reviews_count = int(review_data.get("paging", {}).get("total") or 0)

    manufacturer = "Não informado"
    for attr in item.get("attributes", []):
        if attr.get("id") in {"BRAND", "MANUFACTURER"}:
            manufacturer = attr.get("value_name") or manufacturer
            break

    title = item.get("title", "Sem título")
    price = float(item.get("price") or 0)
    sold = int(item.get("sold_quantity") or 0)
    comparison = _ml_price_comparison(title, price)

    return {
        "url": url,
        "title": title,
        "manufacturer": manufacturer,
        "price": price,
        "sales_count": sold,
        "reviews_count": reviews_count,
        "rating": rating_avg,
        "reviews_quality": _reviews_quality(rating_avg),
        "price_vs_competitors_percent": comparison,
    }


def _ml_price_comparison(title: str, price: float) -> float:
    resp = requests.get(
        f"https://api.mercadolibre.com/sites/MLB/search?q={quote_plus(title[:60])}&limit=20",
        timeout=DEFAULT_TIMEOUT,
    )
    if not resp.ok:
        return 0.0
    prices = [float(x.get("price") or 0) for x in resp.json().get("results", []) if float(x.get("price") or 0) > 0]
    if not prices or price <= 0:
        return 0.0
    med = median(prices)
    return round(((price - med) / med) * 100, 2)


def _analyze_amazon(url: str) -> dict:
    resp = requests.get(url, headers=USER_AGENT, timeout=DEFAULT_TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    title = (soup.select_one("#productTitle") or soup.select_one("h1")).get_text(" ", strip=True)
    price_text = ""
    whole = soup.select_one("span.a-price-whole")
    frac = soup.select_one("span.a-price-fraction")
    if whole:
        price_text = whole.get_text(strip=True) + "." + (frac.get_text(strip=True) if frac else "00")
    price = _parse_decimal_br(price_text)

    rating_text = (soup.select_one("span.a-icon-alt") or {}).get_text("", strip=True) if soup.select_one("span.a-icon-alt") else ""
    rating = _extract_first_number(rating_text)
    reviews_text = (soup.select_one("#acrCustomerReviewText") or {}).get_text("", strip=True) if soup.select_one("#acrCustomerReviewText") else ""
    reviews_count = int(_extract_first_number(reviews_text.replace(".", "")))

    bought_text = soup.get_text(" ", strip=True)
    sales_count = _extract_sales_from_text(bought_text)

    manufacturer = "Não informado"
    byline = soup.select_one("#bylineInfo")
    if byline:
        manufacturer = byline.get_text(" ", strip=True)

    comparison = _amazon_price_comparison(title, price)

    return {
        "url": url,
        "title": title,
        "manufacturer": manufacturer,
        "price": price,
        "sales_count": sales_count,
        "reviews_count": reviews_count,
        "rating": rating,
        "reviews_quality": _reviews_quality(rating),
        "price_vs_competitors_percent": comparison,
    }


def _amazon_price_comparison(title: str, price: float) -> float:
    resp = requests.get(f"https://www.amazon.com.br/s?k={quote_plus(title[:50])}", headers=USER_AGENT, timeout=DEFAULT_TIMEOUT)
    if not resp.ok:
        return 0.0
    soup = BeautifulSoup(resp.text, "html.parser")
    cards = soup.select("div.s-result-item[data-asin]")[:20]
    prices: list[float] = []
    for card in cards:
        whole = card.select_one("span.a-price-whole")
        frac = card.select_one("span.a-price-fraction")
        if not whole:
            continue
        value = _parse_decimal_br(whole.get_text(strip=True) + "." + (frac.get_text(strip=True) if frac else "00"))
        if value > 0:
            prices.append(value)
    if not prices or price <= 0:
        return 0.0
    med = median(prices)
    return round(((price - med) / med) * 100, 2)


def _analyze_shopee(url: str) -> dict:
    match = re.search(r"i\.(\d+)\.(\d+)", url)
    if not match:
        raise ValueError("Não foi possível identificar shopid/itemid no link da Shopee.")
    shopid, itemid = match.group(1), match.group(2)

    resp = requests.get(
        f"https://shopee.com.br/api/v4/item/get?itemid={itemid}&shopid={shopid}",
        headers={**USER_AGENT, "Referer": "https://shopee.com.br/"},
        timeout=DEFAULT_TIMEOUT,
    )
    resp.raise_for_status()
    item = resp.json().get("data", {})

    rating = float(item.get("item_rating", {}).get("rating_star") or 0)
    reviews_count = int(item.get("cmt_count") or 0)
    sales_count = int(item.get("historical_sold") or 0)
    title = item.get("name") or "Sem título"
    manufacturer = item.get("brand") or "Não informado"
    price = float(item.get("price_min") or 0) / 100000

    comparison = _shopee_price_comparison(title, price)

    return {
        "url": url,
        "title": title,
        "manufacturer": manufacturer,
        "price": price,
        "sales_count": sales_count,
        "reviews_count": reviews_count,
        "rating": rating,
        "reviews_quality": _reviews_quality(rating),
        "price_vs_competitors_percent": comparison,
    }


def _shopee_price_comparison(title: str, price: float) -> float:
    resp = requests.get(
        "https://shopee.com.br/api/v4/search/search_items"
        f"?by=relevancy&keyword={quote_plus(title[:50])}&limit=20&newest=0&order=desc&page_type=search",
        headers={**USER_AGENT, "Referer": "https://shopee.com.br/"},
        timeout=DEFAULT_TIMEOUT,
    )
    if not resp.ok:
        return 0.0
    items = resp.json().get("items", [])
    prices = [float(it.get("item_basic", {}).get("price_min") or 0) / 100000 for it in items]
    prices = [p for p in prices if p > 0]
    if not prices or price <= 0:
        return 0.0
    med = median(prices)
    return round(((price - med) / med) * 100, 2)


def _parse_decimal_br(text: str) -> float:
    text = text.strip().replace("R$", "").replace(" ", "")
    if not text:
        return 0.0
    cleaned = text.replace(".", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def _extract_first_number(text: str) -> float:
    match = re.search(r"(\d+[\.,]?\d*)", text)
    if not match:
        return 0.0
    return float(match.group(1).replace(".", "").replace(",", "."))


def _extract_sales_from_text(text: str) -> int:
    patterns = [r"(\d+[\d\.]*)\+?\s*comprados", r"(\d+[\d\.]*)\+?\s*vendas"]
    low = text.lower()
    for pat in patterns:
        m = re.search(pat, low)
        if m:
            return int(m.group(1).replace(".", ""))
    return 0


def _reviews_quality(rating: float) -> str:
    if rating >= 4.3:
        return "Boas"
    if rating >= 3.7:
        return "Médias"
    return "Ruins"


def _is_good_to_sell(data: dict, lucro_percent: float) -> str:
    sales = int(data.get("sales_count") or 0)
    rating = float(data.get("rating") or 0)
    if sales >= 100 and rating >= 4.0 and lucro_percent >= 12:
        return "Sim"
    if lucro_percent >= 8 and rating >= 3.8:
        return "Talvez"
    return "Não"


def _build_improvement_tips(data: dict) -> dict:
    tips = {
        "titulo": "Mantenha título com marca + modelo + benefício principal e palavras-chave de busca.",
        "descricao": "Inclua diferenciais, medidas, garantia e FAQ para reduzir dúvidas.",
        "fotos": "Use no mínimo 6 fotos (fundo branco, uso real e detalhes).",
        "capa": "Capa com produto centralizado, alta resolução e sem poluição visual.",
        "preco": ""
    }

    price_delta = float(data.get("price_vs_competitors_percent") or 0)
    if price_delta > 8:
        tips["preco"] = "Preço acima da mediana da concorrência. Considere reduzir ou agregar valor (kit/frete)."
    elif price_delta < -8:
        tips["preco"] = "Preço abaixo da mediana. Verifique se há margem para aumentar sem perder conversão."
    else:
        tips["preco"] = "Preço competitivo em relação aos concorrentes." 

    return tips
