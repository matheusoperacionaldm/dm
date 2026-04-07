# Analisador local de produto por link (Mercado Livre, Amazon e Shopee)

Aplicação local em Python + HTML para pequenas empresas independentes (micro-saas local): você cola o link de um produto e o sistema detecta automaticamente a plataforma, analisa os dados principais e salva o histórico localmente.

## Funcionalidades principais

- Detecta automaticamente se o link é de:
  - Mercado Livre
  - Amazon
  - Shopee
- Extrai e analisa:
  - Número de vendas
  - Número de avaliações
  - Qualidade das avaliações (boas/médias/ruins)
  - Fabricante / marca
  - Lucro estimado (%)
  - Impostos/Taxas (%)
  - Comparação de preço com concorrentes
  - Recomendação de venda (sim/talvez/não)
- Gera sugestões de melhoria para:
  - Título
  - Descrição
  - Fotos
  - Capa
  - Preço
- Salva automaticamente histórico local em `research_history/`.

## Instalação

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Executar localmente

```bash
python3 app.py
```

Acesse:

- `http://127.0.0.1:5000`

## Armazenamento local

Cada análise é salva em arquivo JSON dentro da pasta:

- `research_history/`

## Observações importantes

- A coleta depende de endpoints públicos e estrutura atual das páginas das plataformas.
- Se a plataforma alterar o layout/API, pode ser necessário ajustar os parsers.
- Todo processamento é local, sem dependência de banco externo.
