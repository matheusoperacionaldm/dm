# Sistema local de pesquisa de mercado (Mercado Livre, Amazon e Shopee)

Projeto em Python para análise de oportunidades de produto com base em dados locais (CSV), sem depender de serviços externos.

## O que o sistema calcula

- Produtos mais vendidos (agregado das três plataformas).
- Número aproximado de vendas mensais.
- Receita mensal estimada.
- Lucro mensal estimado.
- Porcentagem de aproveitamento (margem estimada).
- Recomendação final:
  - `Vale a pena`
  - `Teste em lote pequeno`
  - `Não vale a pena`

## Requisitos

- Python 3.11+

## Instalação

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Formato do CSV

O arquivo deve conter as colunas:

- `platform` (mercado livre, amazon, shopee)
- `product_name`
- `category`
- `seller`
- `unit_price_brl`
- `units_sold_last_30d`
- `shipping_cost_brl`
- `product_cost_brl`
- `ad_cost_brl`
- `marketplace_fee_percent`

Você pode usar `sample_data.csv` como modelo inicial.

## Rodar localmente (HTML + Python)

Suba a aplicação web local em Flask:

```bash
python3 app.py
```

Abra no navegador:

- `http://127.0.0.1:5000`

No site, envie seu CSV e clique em **Analisar** para ver a tabela com métricas.

## Rodar localmente via terminal (CLI)

```bash
python3 main.py sample_data.csv
```

Com margem mínima personalizada e saída em JSON:

```bash
python3 main.py sample_data.csv --min-aproveitamento 10 --output-json resultado.json
```

## Testes

```bash
pytest
```

## Observações

- O sistema é **100% local**: você alimenta os dados via CSV exportado/manual.
- A acurácia depende da qualidade dos dados de entrada.
- Para produção, você pode automatizar exportações e agendar execuções.
