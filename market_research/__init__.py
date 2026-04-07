"""Sistema local de pesquisa de mercado para marketplaces."""

from .analyzer import OpportunityAnalyzer
from .models import ProductListing, ProductOpportunity

__all__ = ["OpportunityAnalyzer", "ProductListing", "ProductOpportunity"]
