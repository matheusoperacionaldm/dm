from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ProductListing:
    """Representa um anúncio bruto extraído de um marketplace."""

    platform: str
    product_name: str
    category: str
    seller: str
    unit_price_brl: float
    units_sold_last_30d: int
    shipping_cost_brl: float
    product_cost_brl: float
    ad_cost_brl: float
    marketplace_fee_percent: float


@dataclass(slots=True)
class ProductOpportunity:
    """Resultado consolidado por produto com métricas de oportunidade."""

    product_name: str
    category: str
    monthly_units_estimated: int
    monthly_revenue_estimated_brl: float
    monthly_profit_estimated_brl: float
    aproveitamento_percent: float
    market_share_percent: float
    recommendation: str
