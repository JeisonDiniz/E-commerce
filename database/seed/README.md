# Dados sintéticos de vendas (Etapa 6)

Este diretório gera um dataset sintético de vendas de roupas — com sazonalidade,
categorias, tamanhos, cores e preços — para treinar/testar os modelos de ML
localmente, com ou sem o Postgres no ar.

## 1. Gerar apenas o dataset (CSV, sem precisar de banco)

Útil para experimentar os modelos (Prophet/Random Forest) direto em pandas,
antes mesmo de o back-end estar rodando.

```bash
cd database/seed
pip install pandas numpy   # se ainda não tiver no ambiente usado
python generate_synthetic_sales.py --start 2024-01-01 --end 2025-12-31
```

Gera em `database/seed/output/`:

| Arquivo | Conteúdo |
|---|---|
| `categories.csv` | 10 categorias (8 de primeiro nível + 2 subcategorias de "Acessórios") |
| `products.csv` | ~24 produtos, cada um com categoria, marca, gênero, estação e preço base |
| `variants.csv` | ~400 variantes (produto × tamanho × cor), com SKU e preço |
| `sales_history.csv` | histórico diário de vendas por variante (o dataset principal para ML) |

Colunas de `sales_history.csv` (mesmo formato da view `vw_daily_sales` do Postgres):
`sku, product_slug, category_slug, gender, season, size, color, price, sale_date, units_sold, revenue`.

### Padrões de sazonalidade embutidos propositalmente

| Padrão | Efeito | Por quê |
|---|---|---|
| Dia da semana | Sex/Sáb/Dom vendem mais (~+15 a +40%) | Comportamento típico de e-commerce de moda |
| Estação do produto | Peças de verão vendem ~3x mais Dez-Mar; inverno ~3x mais Jun-Ago | O que o Prophet deve capturar como sazonalidade anual |
| Black Friday | Pico de ~3.5x na última sexta de novembro | Data comercial mais forte do varejo brasileiro |
| Natal (15–24/dez) | Pico de ~2.3x | Sazonalidade de fim de ano |
| Dia das Mães | Pico de ~2.2x em produtos femininos | Sazonalidade de categoria + data comercial |
| Dia dos Namorados | Pico de ~1.6x geral | — |
| Volta às aulas (jan/fev) | Leve alta em acessórios | — |
| Popularidade por variante (log-normal) | Poucos best-sellers, muitos itens medianos, alguns "parados" | Reproduz o problema real de excesso de estoque parado citado no TCC |
| Tendência | Crescimento linear de ~30% ao longo do período | Loja em expansão |

Validado empiricamente (ver histórico da sessão): produtos de inverno somam ~3.000 unidades/mês em Jun-Ago contra ~1.000/mês no resto do ano; Black Friday chega a ~260 unidades/dia contra uma média de ~90/dia em novembro.

## 2. Popular o Postgres (banco de demonstração completo)

Depois de aplicar `database/schema.sql` e configurar `backend/.env`:

```bash
cd backend
.venv/Scripts/activate
python -m scripts.seed_database              # primeira carga
python -m scripts.seed_database --reset       # apaga tudo e recarrega do zero
```

O script (`backend/scripts/seed_database.py`) usa os mesmos módulos deste
diretório para gerar os dados e então:

- Cria 3 contas de staff (`admin@loja.com`, `gestor@loja.com`, `estoque@loja.com`) e 40 clientes fictícios, todos com senha `Senha@123`.
- Insere categorias, produtos, variantes e o estoque **atual**.
- Materializa cada linha do histórico sintético como um pedido completo (`orders` + `order_items` + `payments` + `inventory_movements` do tipo `saida`), com `created_at` igual à data histórica da venda — essencial para o Prophet enxergar sazonalidade real ao consultar `vw_daily_sales`.
- Gera movimentos de `entrada` mensais por variante (reposição), para o livro-razão de estoque não conter só saídas.
- Registra um reajuste de preço sintético (`price_logs`) para ~15% das variantes.

### Estoque atual: propostalmente desbalanceado

O saldo em `inventory.quantity` **não** é recalculado a partir do replay de
todos os movimentos históricos — ele é definido diretamente a partir do
volume de vendas de cada SKU no dataset sintético:

- **20% dos SKUs menos vendidos** recebem estoque alto (150–300 un.) → simula **excesso de estoque parado**.
- **20% dos SKUs mais vendidos** recebem estoque baixo (0–4 un.) → simula **risco de ruptura**.
- Os 60% restantes recebem estoque moderado (20–60 un.).

Essa é uma simplificação deliberada (documentada aqui para a defesa do TCC):
gerar um "livro-razão" 100% consistente do zero exigiria simular compras e
vendas em paralelo por dois anos com contabilidade de estoque perfeita, o que
adicionaria complexidade sem valor para o objetivo do dataset (treinar/testar
os modelos de ML e demonstrar o dashboard de estoque).
