# Front-end — React (Vite + TypeScript)

## Stack e por quê

- **Vite + React + TypeScript** — build rápido, tipagem estática ajuda a manter os contratos com a API do back-end (schemas em `src/types/index.ts` espelham os schemas Pydantic).
- **React Router** — separa claramente a loja pública (`/`, `/produtos/:id`, `/carrinho`, `/checkout`, `/meus-pedidos`) do painel administrativo (`/admin/*`), com guardas de rota por papel (`src/routes/ProtectedRoute.tsx`).
- **Zustand** — gerenciamento de estado global mínimo e sem boilerplate, usado para autenticação (`store/authStore.ts`, persistido em `localStorage`) e carrinho (`store/cartStore.ts`, sincronizado com a API).
- **Axios** — cliente HTTP único (`api/client.ts`) com interceptor que injeta o JWT em toda requisição e desloga automaticamente em 401.
- **Recharts** — gráficos do dashboard administrativo, com paleta e especificações de marca (cores categóricas, espessura de linha, faixa de confiança) seguindo a metodologia de visualização de dados do projeto (ver `src/components/charts/palette.ts`).
- **Tailwind CSS v4** — estilização utilitária, sem necessidade de escrever CSS customizado para cada componente.

## Estrutura de pastas

```
src/
├── api/            # funções tipadas por domínio (auth, catalog, cart, orders, inventory, reports, predictions)
├── types/           # interfaces TS espelhando os schemas Pydantic do back-end
├── store/            # estado global (zustand): autenticação e carrinho
├── components/
│   ├── layout/        # StorefrontLayout (header/nav da loja) e AdminLayout (sidebar)
│   ├── ui/              # primitivos reutilizáveis: Button, Card, Badge, Spinner, EmptyState
│   ├── product/          # ProductCard
│   └── charts/            # StatTile, SalesLineChart, TopProductsBarChart, CategoryTrendChart, palette.ts
├── pages/
│   ├── storefront/          # Home (catálogo), ficha de produto, carrinho, checkout, pedidos, login/cadastro
│   └── admin/                # Dashboard (gráficos de ML), produtos, estoque, sugestões de reposição, pedidos
└── routes/                     # RequireAuth / RequireStaff (guardas de rota por papel)
```

## Como rodar

```bash
cd frontend
npm install
npm run dev
```

O Vite faz proxy de `/api/*` para `http://localhost:8000` (ver `vite.config.ts`), então basta o back-end (Etapa 2) estar rodando em `localhost:8000` — o front-end não precisa de nenhuma variável de ambiente própria em desenvolvimento.

## Contas de demonstração

Depois de rodar `python -m scripts.seed_database` no back-end (Etapa 6):

| Papel | E-mail | Senha |
|---|---|---|
| Admin | admin@loja.com | Senha@123 |
| Gestor de estoque | gestor@loja.com | Senha@123 |
| Operador de estoque | estoque@loja.com | Senha@123 |
| Cliente | cliente1@exemplo.com (…até cliente40) | Senha@123 |

## Painel administrativo

- **Dashboard** (`/admin`): estatísticas de estoque, vendas diárias, produtos mais vendidos e a previsão de tendência por categoria (Prophet, com faixa de confiança) — este último gráfico só mostra dados depois de rodar `python -m app.ml.train --source db` no back-end.
- **Sugestões de reposição** (`/admin/reposicao`): lista as sugestões geradas pelo Random Forest; aprovar/rejeitar é sempre uma decisão humana — nenhuma reposição é feita automaticamente.
- **Estoque** (`/admin/estoque`): registra movimentações (entrada/saída/ajuste/devolução) e lista itens em risco de ruptura.