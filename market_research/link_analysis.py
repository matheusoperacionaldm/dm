from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from statistics import mean, median
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
    sales_last_30d = int(data.get("sales_last_30d") or 0)
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
            "is_good_to_sell": _is_good_to_sell(sales_last_30d),
            "improvements": _build_improvement_tips(data),
            "analyzed_at": datetime.utcnow().isoformat() + "Z",
        }
    )
    saved = save_analysis(data)
    data["saved_file"] = str(saved)
    data["saved_file_name"] = saved.name
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


def clear_history() -> int:
    if not HISTORY_DIR.exists():
        return 0
    count = 0
    for file in HISTORY_DIR.glob("*.json"):
        file.unlink(missing_ok=True)
        count += 1
    return count


def _analyze_mercado_livre(url: str) -> dict:
    item_id_match = re.search(r"(MLB-?\d+)", url.upper())
    if not item_id_match:
        raise ValueError("Não foi possível identificar o item do Mercado Livre no link.")
    item_id = item_id_match.group(1).replace("-", "")

    item = requests.get(f"https://api.mercadolibre.com/items/{item_id}", timeout=DEFAULT_TIMEOUT).json()

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
    sales_last_30d = int(item.get("sold_quantity") or 0)
    stats = _ml_price_stats(title)

    return {
        "url": url,
        "title": title,
        "manufacturer": manufacturer,
        "price": price,
        "sales_last_30d": sales_last_30d,
        "sales_count": sales_last_30d,
        "reviews_count": reviews_count,
        "rating": rating_avg,
        "reviews_quality": _reviews_quality(rating_avg),
        "price_stats": stats,
        "price_vs_competitors_percent": _percent_delta(price, stats["avg_price"]),
    }


def _ml_price_stats(title: str) -> dict:
    resp = requests.get(
        f"https://api.mercadolibre.com/sites/MLB/search?q={quote_plus(title[:60])}&limit=50",
        timeout=DEFAULT_TIMEOUT,
    )
    if not resp.ok:
        return _empty_price_stats()
    items = resp.json().get("results", [])
    points = [(float(x.get("price") or 0), int(x.get("sold_quantity") or 0)) for x in items]
    return _build_price_stats(points)


def _analyze_amazon(url: str) -> dict:
    resp = requests.get(url, headers=USER_AGENT, timeout=DEFAULT_TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    title = (soup.select_one("#productTitle") or soup.select_one("h1")).get_text(" ", strip=True)
    whole = soup.select_one("span.a-price-whole")
    frac = soup.select_one("span.a-price-fraction")
    price = _parse_decimal_br((whole.get_text(strip=True) if whole else "") + "." + (frac.get_text(strip=True) if frac else "00"))

    rating_text = soup.select_one("span.a-icon-alt")
    rating = _extract_first_number(rating_text.get_text("", strip=True) if rating_text else "")
    reviews_text = soup.select_one("#acrCustomerReviewText")
    reviews_count = int(_extract_first_number(reviews_text.get_text("", strip=True).replace(".", "") if reviews_text else ""))

    sales_last_30d = _extract_sales_from_text(soup.get_text(" ", strip=True))
    manufacturer = (soup.select_one("#bylineInfo").get_text(" ", strip=True) if soup.select_one("#bylineInfo") else "Não informado")
    stats = _amazon_price_stats(title)

    return {
        "url": url,
        "title": title,
        "manufacturer": manufacturer,
        "price": price,
        "sales_last_30d": sales_last_30d,
        "sales_count": sales_last_30d,
        "reviews_count": reviews_count,
        "rating": rating,
        "reviews_quality": _reviews_quality(rating),
        "price_stats": stats,
        "price_vs_competitors_percent": _percent_delta(price, stats["avg_price"]),
    }


def _amazon_price_stats(title: str) -> dict:
    resp = requests.get(f"https://www.amazon.com.br/s?k={quote_plus(title[:50])}", headers=USER_AGENT, timeout=DEFAULT_TIMEOUT)
    if not resp.ok:
        return _empty_price_stats()
    soup = BeautifulSoup(resp.text, "html.parser")
    cards = soup.select("div.s-result-item[data-asin]")[:50]
    points: list[tuple[float, int]] = []
    for card in cards:
        whole = card.select_one("span.a-price-whole")
        frac = card.select_one("span.a-price-fraction")
        if not whole:
            continue
        price = _parse_decimal_br(whole.get_text(strip=True) + "." + (frac.get_text(strip=True) if frac else "00"))
        sales = _extract_sales_from_text(card.get_text(" ", strip=True))
        points.append((price, sales))
    return _build_price_stats(points)


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
    sales_last_30d = int(item.get("historical_sold") or 0)
    title = item.get("name") or "Sem título"
    manufacturer = item.get("brand") or "Não informado"
    price = float(item.get("price_min") or 0) / 100000
    stats = _shopee_price_stats(title)

    return {
        "url": url,
        "title": title,
        "manufacturer": manufacturer,
        "price": price,
        "sales_last_30d": sales_last_30d,
        "sales_count": sales_last_30d,
        "reviews_count": reviews_count,
        "rating": rating,
        "reviews_quality": _reviews_quality(rating),
        "price_stats": stats,
        "price_vs_competitors_percent": _percent_delta(price, stats["avg_price"]),
    }


def _shopee_price_stats(title: str) -> dict:
    resp = requests.get(
        "https://shopee.com.br/api/v4/search/search_items"
        f"?by=relevancy&keyword={quote_plus(title[:50])}&limit=50&newest=0&order=desc&page_type=search",
        headers={**USER_AGENT, "Referer": "https://shopee.com.br/"},
        timeout=DEFAULT_TIMEOUT,
    )
    if not resp.ok:
        return _empty_price_stats()
    items = resp.json().get("items", [])
    points = [
        (
            float(it.get("item_basic", {}).get("price_min") or 0) / 100000,
            int(it.get("item_basic", {}).get("historical_sold") or 0),
        )
        for it in items
    ]
    return _build_price_stats(points)


def _build_price_stats(points: list[tuple[float, int]]) -> dict:
    points = [(price, sold) for price, sold in points if price > 0]
    if not points:
        return _empty_price_stats()
    prices = [price for price, _ in points]
    avg_price = round(mean(prices), 2)
    min_price, min_sales = min(points, key=lambda x: x[0])
    max_price, max_sales = max(points, key=lambda x: x[0])
    return {
        "avg_price": avg_price,
        "min_price": round(min_price, 2),
        "min_price_sales": int(min_sales),
        "max_price": round(max_price, 2),
        "max_price_sales": int(max_sales),
    }


def _empty_price_stats() -> dict:
    return {"avg_price": 0.0, "min_price": 0.0, "min_price_sales": 0, "max_price": 0.0, "max_price_sales": 0}


def _percent_delta(price: float, base: float) -> float:
    if price <= 0 or base <= 0:
        return 0.0
    return round(((price - base) / base) * 100, 2)


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
    patterns = [r"(\d+[\d\.]*)\+?\s*comprados", r"(\d+[\d\.]*)\+?\s*vendas", r"mês passado\D*(\d+[\d\.]*)"]
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


def _is_good_to_sell(sales_last_30d: int) -> str:
    if sales_last_30d > 500:
        return "Bom para vender"
    return "Ruim para vender"


def _build_improvement_tips(data: dict) -> dict:
    rating = float(data.get("rating") or 0)
    reviews_count = int(data.get("reviews_count") or 0)
    sales = int(data.get("sales_last_30d") or 0)
    delta = float(data.get("price_vs_competitors_percent") or 0)

    tips = {
        "titulo": "Use marca + modelo + principal atributo técnico + palavra-chave de busca com alto volume.",
        "descricao": "Detalhar ficha técnica, compatibilidade, garantia, prazos e objeções comuns para aumentar conversão.",
        "fotos": "Adicionar fotos em alta resolução com zoom, contexto de uso e detalhes de acabamento/medidas.",
        "capa": "A capa deve mostrar o benefício principal em primeiro olhar, com fundo limpo e boa iluminação.",
        "preco": "Preço dentro da faixa média da plataforma.",
        "avaliacoes": "Volume e nota de avaliações em linha com concorrentes.",
    }

    if delta > 8:
        tips["preco"] = "Preço acima da média da plataforma. Avalie redução ou oferta de valor adicional (kit/frete/garantia)."
    elif delta < -8:
        tips["preco"] = "Preço abaixo da média. Verifique se existe margem para ajuste sem perder competitividade."

    if reviews_count < 30 or rating < 4.0:
        tips["avaliacoes"] = "Fortalecer pós-venda para aumentar avaliações e melhorar nota média (meta: >=4.3)."

    if sales < 100:
        tips["descricao"] += " Reforce diferenciais e prova social para elevar vendas nos próximos 30 dias."

    return tips
