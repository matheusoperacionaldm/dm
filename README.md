# Sistema local de pesquisa de mercado (Mercado Livre, Amazon e Shopee)

Projeto em Python para análise de oportunidades de produto sem CSV, buscando automaticamente anúncios nas plataformas selecionadas.

## O que o sistema calcula automaticamente

- Produtos com maior índice de venda por termo pesquisado.
- Número aproximado de vendas mensais.
- Receita mensal estimada.
- Lucro mensal estimado.
- Lucro (%).
- Aproveitamento de vendas (%).
- Impostos/Taxas de marketplace (% médio por produto).
- Recomendação final (`Vale a pena`, `Teste em lote pequeno`, `Não vale a pena`).

## Requisitos

- Python 3.11+

## Instalação

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Rodar localmente (HTML + Python, sem CSV)

```bash
python3 app.py
```

Abra no navegador:

- `http://127.0.0.1:5000`

No site:

1. Digite o produto (ex.: `fone bluetooth`).
2. Marque Mercado Livre, Amazon e/ou Shopee.
3. Clique em **Analisar automaticamente**.

## Rodar via terminal (CLI, opcional com CSV)

A versão CLI permanece disponível para uso com CSV local:

```bash
python3 main.py sample_data.csv
```

## Observações

- A coleta automática depende da disponibilidade dos endpoints públicos das plataformas.
- Em caso de bloqueio temporário de uma plataforma, as demais continuam sendo analisadas.
- Os percentuais de impostos/taxas são estimados com base em taxa média por marketplace.
