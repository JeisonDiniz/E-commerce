# Módulo de Machine Learning

```
app/ml/
├── features.py            # carrega histórico (CSV ou vw_daily_sales) + engenharia de features
├── holidays.py             # calendário de datas comerciais (BR) usado pelo Prophet
├── prophet_model.py         # treino/avaliação/previsão futura — série por categoria
├── random_forest_model.py   # pipeline scikit-learn — demanda por variante
├── train.py                  # orquestração: treina os dois modelos, avalia, grava no Postgres
└── artifacts/                 # modelos treinados (.joblib), gitignored
```

## Fluxo de dados

```
vw_daily_sales (Postgres)  ─┐
                             ├─► features.py ─► prophet_model.py   ─► ml_predictions (category_id)
sales_history.csv (Etapa 6)─┘                └► random_forest_model.py ─► ml_predictions (variant_id)
                                                                    │
                                                                    └─► restock_suggestions (status=pendente)
```

`app/api/v1/endpoints/predictions.py` (Etapa 2) lê dessas mesmas tabelas,
com Redis como cache de leitura — **nenhum código de API precisa mudar**
quando o `train.py` é executado novamente; ele só substitui o conteúdo de
`ml_predictions`/`ml_model_metrics`/`restock_suggestions`, e a próxima leitura
via API repopula o cache automaticamente.

## Por que dois modelos, e não um só

- **Prophet** responde "QUANDO vender mais" — sazonalidade semanal, mensal e
  datas comerciais, por categoria. É a base para decisões de antecipação de
  compra (ex: comprar casacos antes do inverno).
- **Random Forest** responde "O QUE vai vender mais" — dado categoria,
  tamanho, cor e preço de cada variante específica, prevê o volume de demanda
  esperado. É a base para a sugestão de reposição por item.

Um modelo de série temporal (Prophet) não tem como usar atributos categóricos
por item (tamanho/cor) como features; um modelo de regressão tabular (Random
Forest) não modela nativamente sazonalidade de calendário da mesma forma que
o Prophet. Por isso os dois são complementares, e não substituíveis um pelo
outro — exatamente como especificado no projeto de pesquisa do TCC.

## Métricas e critérios de aceitação

Ver [`docs/ml-results.md`](../../../docs/ml-results.md) para os números reais
obtidos, a discussão sobre por que o MAE atende ao critério do TCC e o MAPE
não (piso estatístico de ruído em processos de contagem/Poisson para baixo
volume), e a recomendação de métrica primária para a defesa.

## Rodando o treinamento

```bash
cd backend
.venv/Scripts/activate
python -m app.ml.train --source csv    # offline: só imprime métricas, não toca no banco
python -m app.ml.train --source db     # produção: grava métricas + previsões + sugestões de reposição
```

Pré-requisito do modo `--source csv`: rodar antes o gerador da Etapa 6
(`database/seed/generate_synthetic_sales.py`), que cria
`database/seed/output/sales_history.csv`.
