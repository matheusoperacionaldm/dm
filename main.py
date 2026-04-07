from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from market_research import OpportunityAnalyzer
from market_research.data_loader import load_listings_from_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Sistema local de pesquisa de mercado para Mercado Livre, Amazon e Shopee. "
            "Use um CSV local com dados dos anúncios para gerar estimativas."
        )
    )
    parser.add_argument("csv_file", type=Path, help="Caminho do arquivo CSV de entrada")
    parser.add_argument(
        "--min-aproveitamento",
        type=float,
        default=8.0,
        help="Margem mínima (%) para recomendar o produto",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        help="Opcional: salva o resultado em JSON",
    )
    return parser


def print_report(opportunities: list[dict]) -> None:
    if not opportunities:
        print("Nenhum dado para analisar.")
        return

    header = (
        f"{'Produto':35} {'Vendas/mês':>10} {'Receita (R$)':>14} "
        f"{'Lucro (R$)':>12} {'Aprov.%':>8} {'Share %':>8} {'Decisão':>20}"
    )
    print(header)
    print("-" * len(header))

    for item in opportunities:
        print(
            f"{item['product_name'][:35]:35} "
            f"{item['monthly_units_estimated']:10d} "
            f"{item['monthly_revenue_estimated_brl']:14.2f} "
            f"{item['monthly_profit_estimated_brl']:12.2f} "
            f"{item['aproveitamento_percent']:8.2f} "
            f"{item['market_share_percent']:8.2f} "
            f"{item['recommendation']:>20}"
        )


def main() -> None:
    args = build_parser().parse_args()
    listings = load_listings_from_csv(args.csv_file)
    analyzer = OpportunityAnalyzer(min_aproveitamento_percent=args.min_aproveitamento)
    results = [asdict(row) for row in analyzer.analyze(listings)]

    print_report(results)

    if args.output_json:
        args.output_json.write_text(
            json.dumps(results, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"\nJSON salvo em: {args.output_json}")


if __name__ == "__main__":
    main()
