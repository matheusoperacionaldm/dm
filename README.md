# Analisador local de produto por link (Mercado Livre, Amazon e Shopee)

Aplicação local em Python + HTML para micro-saas e pequenas empresas independentes.

## Funcionalidades

- Análise automática por link do produto (detecção da plataforma).
- Número de vendas nos últimos 30 dias.
- Qualidade das avaliações com nota e quantidade de avaliações.
- Fabricante do produto.
- Lucro estimado (%), impostos/taxas (%).
- Classificação de venda:
  - **Bom para vender**: mais de 500 vendas nos últimos 30 dias.
  - **Ruim para vender**: poucas vendas nos últimos 30 dias.
- Preço médio, menor preço e maior preço da plataforma + vendas nesses preços.
- Melhorias detalhadas de título, descrição, fotos, capa, preço e avaliações.
- Histórico local em `research_history/`.
- Botão para limpar pesquisas locais.
- Interface moderna com alternância de tema claro/escuro.

## Instalação

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Executar

```bash
python3 app.py
```

Acesse `http://127.0.0.1:5000`.

## Observações

- A precisão depende dos dados disponíveis publicamente em cada plataforma.
- Caso uma plataforma altere estrutura de página/API, os parsers podem precisar de ajuste.
- O processamento e armazenamento são locais.
