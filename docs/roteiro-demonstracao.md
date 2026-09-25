# Roteiro de demonstração (defesa do TCC)

Script para a apresentação ao vivo do sistema. Pensado para ~12–15 minutos
de demo, cobrindo loja, painel administrativo e o módulo de Machine
Learning — nessa ordem, do ponto de vista do cliente até o do gestor.

## Antes de começar (checklist de preparação)

- [ ] `docker compose up -d` (Postgres + Redis) e confirmar `docker compose ps` com os dois "healthy"/"Up"
- [ ] Back-end: `cd backend && uvicorn app.main:app --reload` — conferir `http://localhost:8000/health` → `{"status":"ok"}`
- [ ] Front-end: `cd frontend && npm run dev` — abrir `http://localhost:5173`
- [ ] Banco populado: `python -m scripts.seed_database` (se ainda não rodou nesta máquina)
- [ ] Modelos treinados: `python -m app.ml.train --source db` (grava previsões e sugestões de reposição — sem isso o dashboard e a página de sugestões aparecem vazios)
- [ ] Ter pelo menos **duas fotos de produto** cadastradas (uma por cor) em pelo menos um produto — evita improvisar upload ao vivo se a rede da sala for instável (mas o passo 3 abaixo mostra como fazer isso ao vivo também)
- [ ] Guia de credenciais de demonstração em mãos (tabela no README — `admin@loja.com` / `gestor@loja.com` / `estoque@loja.com`, senha `Senha@123`)
- [ ] Navegador com zoom em 100% e janela redimensionável à mão, para o passo 6 (responsividade)

## 1. Contexto (1 min, sem tela)

Frase de abertura: "Loja virtual de moda que une e-commerce, controle de
estoque e Machine Learning num único sistema — a diferença para soluções de
mercado é que a decisão de repor estoque nunca é automática: o modelo
**sugere**, um gestor humano **aprova**."

## 2. Loja — jornada do cliente (4 min)

1. Abrir a home (`/`) — mostrar filtro por categoria, busca, filtro de tamanho/preço.
2. Abrir um produto com fotos cadastradas.
3. Clicar em cada cor disponível — **destacar que a galeria de fotos troca
   junto com a cor selecionada** (é a feature mais visual do sistema).
4. Selecionar tamanho, adicionar à sacola.
5. Ir ao carrinho, ajustar quantidade, mostrar subtotal/total formatados em `R$`.
6. Seguir para o checkout, preencher/selecionar endereço, escolher forma de
   pagamento, finalizar o pedido.
7. Abrir "Meus pedidos" e mostrar o pedido recém-criado com status.

## 3. Painel administrativo — catálogo e imagens (3 min)

1. Logar como `gestor@loja.com`.
2. Ir em Produtos → abrir "Gerenciar fotos" de um produto.
3. Selecionar uma cor, escolher um arquivo, mostrar o preview antes de
   enviar, clicar em "Enviar imagem" — a foto aparece na hora na lista,
   agrupada por cor. (Se quiser mostrar ao vivo a galeria mudando: repita o
   passo 3 no navegador do cliente enquanto o upload já estiver feito.)
4. Mostrar a validação: tentar subir um arquivo que não é imagem ou maior
   que 5MB e mostrar a mensagem de erro.

## 4. Painel administrativo — estoque (2 min)

1. Ir em Estoque → registrar uma movimentação (entrada/saída) para uma
   variante e mostrar o saldo atualizando.
2. Mostrar a lista de "Itens em risco de ruptura".

## 5. Machine Learning — o diferencial do TCC (4 min)

1. Ir em Dashboard → mostrar os KPIs (variantes cadastradas, unidades em
   estoque, faturamento) e os dois gráficos (vendas diárias, produtos mais
   vendidos).
2. Trocar a categoria no gráfico "Tendência de demanda (Prophet)" e mostrar
   a curva de previsão com sazonalidade.
3. Ir em "Sugestões de reposição" → mostrar uma sugestão pendente gerada
   pelo Random Forest, **aprovar uma e rejeitar outra** — reforçar que isso
   gera (ou não) uma movimentação de estoque real, nunca automática.
4. Abrir `docs/ml-results.md` (ou ter os números decorados) e comentar:
   MAE atende a meta do TCC nos dois modelos; o MAPE não atende, e explicar
   em uma frase o porquê (piso estatístico de ruído em processos de
   contagem de baixo volume — não é erro de implementação).

## 6. Qualidade e segurança (2 min, opcional se sobrar tempo)

1. Redimensionar a janela do navegador ao vivo (desktop → mobile) na home e
   no painel admin, mostrando que o layout se adapta sem quebrar.
2. Mencionar (sem precisar demonstrar) os pontos de `SECURITY.md`: senhas
   com bcrypt, JWT, RBAC por papel, upload de imagem validado, rate
   limiting de login, sem SQL injection (ORM parametrizado).
3. Abrir `/docs` (Swagger) rapidamente para mostrar a documentação
   automática da API.

## Perguntas prováveis da banca (respostas curtas)

- **"Por que Prophet e Random Forest, e não só um?"** — Prophet captura
  sazonalidade/tendência agregada por categoria (útil para planejamento);
  Random Forest prevê demanda por variante específica (tamanho/cor), que é
  o nível de granularidade que o gestor realmente precisa para decidir
  quanto repor.
- **"Por que o MAPE não bateu a meta?"** — ver seção 5.4 e `docs/ml-results.md`
  — é um limite estatístico do processo (baixo volume diário), não uma
  falha do modelo; o MAE (métrica que o negócio usa de fato) bate a meta
  nos dois casos.
- **"O sistema está pronto para produção real?"** — funcionalmente sim; o
  `SECURITY.md` documenta o que ainda depende do ambiente de deploy (TLS,
  segredo forte, backups) — não é código, é operação.
- **"Como as imagens são armazenadas?"** — localmente em disco por trás de
  uma abstração (`StorageBackend`); trocar para um provedor de nuvem no
  deploy é implementar uma nova classe, sem mudar API nem front-end.
