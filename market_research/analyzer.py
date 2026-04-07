from __future__ import annotations

from collections import defaultdict

from .models import ProductListing, ProductOpportunity

SUPPORTED_PLATFORMS = {"mercado livre", "amazon", "shopee"}


class OpportunityAnalyzer:
    """Calcula indicadores de demanda, receita e viabilidade."""

    def __init__(self, min_aproveitamento_percent: float = 8.0) -> None:
        self.min_aproveitamento_percent = min_aproveitamento_percent

    def analyze(self, listings: list[ProductListing]) -> list[ProductOpportunity]:
        if not listings:
            return []

        self._validate_platforms(listings)
        grouped = self._group_by_product(listings)
        total_market_units = sum(sum(item.units_sold_last_30d for item in group) for group in grouped.values())

        opportunities: list[ProductOpportunity] = []
        for (_product_key, _category_key), group in grouped.items():
            product_name = group[0].product_name
            category = group[0].category
            monthly_units = sum(item.units_sold_last_30d for item in group)
            avg_price = sum(item.unit_price_brl for item in group) / len(group)
            revenue_estimated = monthly_units * avg_price

            avg_variable_cost = (
                sum(item.product_cost_brl + item.shipping_cost_brl + item.ad_cost_brl for item in group)
                / len(group)
            )
            avg_fee_percent = sum(item.marketplace_fee_percent for item in group) / len(group)
            fee_cost = revenue_estimated * (avg_fee_percent / 100)
            profit_estimated = revenue_estimated - (monthly_units * avg_variable_cost) - fee_cost
            aproveitamento = (profit_estimated / revenue_estimated * 100) if revenue_estimated > 0 else 0.0
            market_share = (monthly_units / total_market_units * 100) if total_market_units else 0.0
            recommendation = self._build_recommendation(aproveitamento, monthly_units)

            opportunities.append(
                ProductOpportunity(
                    product_name=product_name,
                    category=category,
                    monthly_units_estimated=monthly_units,
                    monthly_revenue_estimated_brl=round(revenue_estimated, 2),
                    monthly_profit_estimated_brl=round(profit_estimated, 2),
                    aproveitamento_percent=round(aproveitamento, 2),
                    market_share_percent=round(market_share, 2),
                    recommendation=recommendation,
                )
            )

        return sorted(
            opportunities,
            key=lambda item: (item.aproveitamento_percent, item.monthly_units_estimated),
            reverse=True,
        )

    def _validate_platforms(self, listings: list[ProductListing]) -> None:
        unsupported = {item.platform for item in listings if item.platform not in SUPPORTED_PLATFORMS}
        if unsupported:
            names = ", ".join(sorted(unsupported))
            raise ValueError(
                "Plataformas não suportadas encontradas no CSV: "
                f"{names}. Use apenas Mercado Livre, Amazon e Shopee."
            )

    @staticmethod
    def _group_by_product(listings: list[ProductListing]) -> dict[tuple[str, str], list[ProductListing]]:
        groups: dict[tuple[str, str], list[ProductListing]] = defaultdict(list)
        for item in listings:
            key = (item.product_name.lower(), item.category.lower())
            groups[key].append(item)
        return groups

    def _build_recommendation(self, aproveitamento_percent: float, monthly_units: int) -> str:
        if aproveitamento_percent >= self.min_aproveitamento_percent and monthly_units >= 200:
            return "Vale a pena"
        if aproveitamento_percent >= self.min_aproveitamento_percent and monthly_units < 200:
            return "Teste em lote pequeno"
        return "Não vale a pena"
