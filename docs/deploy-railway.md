# Deploy no Railway

Este guia sobe o projeto inteiro (front-end React + back-end FastAPI) como
**um único serviço** no Railway, mais dois plugins gerenciados (PostgreSQL e
Redis). Um único domínio serve tanto a API (`/api/v1/...`) quanto o site
(`/`), o que evita configurar CORS e evita o problema clássico de URLs
relativas (imagens em `/media/...`, chamadas em `/api/v1/...`) apontarem
para o domínio errado quando front e back moram em serviços separados.

## O que já foi preparado no repositório

- **`Dockerfile`** (raiz): builda o front-end (`npm run build`) e copia o
  resultado para dentro da imagem do back-end, que passa a servi-lo
  diretamente (ver o bloco "Front-end" no fim de
  [backend/app/main.py](../backend/app/main.py)).
- **`backend/requirements-web.txt`**: mesmas dependências de
  `requirements.txt` **sem** pandas/numpy/scikit-learn/prophet/joblib — essas
  libs só são usadas pelo treinamento offline (`python -m app.ml.train`,
  rodado manualmente contra o banco), nunca pela API em si. Isso mantém o
  build da imagem rápido (o `pip install` do prophet compila o CmdStan e é
  pesado/lento).
- **`backend/app/core/config.py`**: `DATABASE_URL` agora normaliza sozinho
  URLs no formato `postgres://...`/`postgresql://...` (o que o Railway
  injeta) para `postgresql+asyncpg://...` (o que o SQLAlchemy async exige).
- `.dockerignore` (raiz e implícito via `.gitignore`) para não copiar
  `node_modules`, `venv`, uploads locais etc. para dentro da imagem.

Isso já foi testado localmente (build do front, import do `app.main`,
servidor rodando com o `frontend_dist` simulado) — falta só configurar o
Railway, que exige uma conta e não pode ser feito por aqui.

## Passo a passo no Railway

### 1. Criar o projeto

1. Suba o repositório para o GitHub (se ainda não estiver lá).
2. Em [railway.app](https://railway.app) → **New Project** → **Deploy from
   GitHub repo** → selecione este repositório.
3. Railway vai criar um serviço a partir do `Dockerfile` da raiz
   automaticamente (ele detecta o `Dockerfile` sozinho). Se perguntar o
   **Root Directory**, deixe a raiz do repo (não `backend/` nem
   `frontend/`) — o Dockerfile precisa enxergar as duas pastas.

### 2. Adicionar PostgreSQL e Redis

No mesmo projeto: **+ New** → **Database** → **Add PostgreSQL**, e de novo
**+ New** → **Database** → **Add Redis**. O Railway cria esses dois serviços
e expõe variáveis como `${{Postgres.DATABASE_URL}}` e
`${{Redis.REDIS_URL}}` que podem ser referenciadas por outros serviços do
mesmo projeto.

### 3. Variáveis de ambiente do serviço web

No serviço web (o que builda o `Dockerfile`) → aba **Variables** → adicione:

| Variável | Valor |
|---|---|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` (referência ao plugin) |
| `REDIS_URL` | `${{Redis.REDIS_URL}}` (referência ao plugin) |
| `ENVIRONMENT` | `production` |
| `SECRET_KEY` | uma string aleatória longa — gere com `python -c "import secrets; print(secrets.token_urlsafe(64))"` (o boot **falha de propósito** se isso ficar com o valor padrão em produção, ver `assert_production_safety`) |
| `CORS_ORIGINS` | pode deixar o valor padrão; como front e back são o mesmo domínio, CORS não entra no caminho das requisições normais |
| `FRONTEND_URL` | preencha depois do passo 4, com a URL pública do próprio serviço (ex.: `https://seu-app.up.railway.app`) — usada no link de "esqueci minha senha" |
| `STORAGE_BACKEND` | `local` (ver aviso sobre uploads no passo 6) |
| `MEDIA_ROOT` | `static/uploads` |
| `MEDIA_BASE_URL` | `/media` |
| `MELHOR_ENVIO_TOKEN` | token da sua conta (sandbox ou produção) em melhorenvio.com.br |
| `MERCADO_PAGO_ACCESS_TOKEN` / `MERCADO_PAGO_PUBLIC_KEY` / `MERCADO_PAGO_WEBHOOK_SECRET` | credenciais do Mercado Pago (ver `docs/frete-e-pagamento.md`) |
| `SMTP_HOST` etc. | opcional; sem isso, o link de redefinição de senha só é logado (visível em **Deployments → Logs**) |

Não defina `PORT` — o Railway injeta essa variável sozinho e o `CMD` do
Dockerfile já usa `${PORT:-8000}`.

### 4. Gerar o domínio público

No serviço web → **Settings** → **Networking** → **Generate Domain**. Isso
dá uma URL do tipo `https://seu-app.up.railway.app`. Volte na aba
**Variables** e preencha `FRONTEND_URL` com essa URL.

### 5. Criar o schema do banco

O projeto **não usa Alembic** — o schema é aplicado direto via
`database/schema.sql`. Como o Postgres do Railway não vem com esse schema,
rode uma vez (a partir da sua máquina, com `psql` instalado):

```bash
# Copie a "Connection URL" pública do plugin Postgres (Settings → aba
# "Connect" → "Public Network"), formato postgresql://user:pass@host:porta/db
psql "COLE_A_CONNECTION_URL_AQUI" -f database/schema.sql
```

Não é preciso rodar os arquivos em `database/migrations/` — eles servem só
para bancos antigos que já existiam antes dessas colunas/tabelas serem
incorporadas ao `schema.sql`; um banco novo já nasce completo.

Opcional — popular com dados de demonstração (catálogo + histórico de
vendas sintético, útil para a defesa do TCC):

```bash
cd backend
# .env local apontando DATABASE_URL para a Connection URL pública acima
python -m scripts.seed_database
```

### 6. Deploy

Com as variáveis configuradas, o Railway já deve ter disparado o primeiro
build a partir do push no GitHub. Acompanhe em **Deployments**. Ao concluir:

- `https://seu-app.up.railway.app/health` → `{"status": "ok"}`
- `https://seu-app.up.railway.app/docs` → Swagger da API
- `https://seu-app.up.railway.app/` → o site (React)

### 7. (Recomendado) Volume para uploads de imagem

O `STORAGE_BACKEND=local` grava as imagens de produto em disco
(`static/uploads` dentro do container). **Sem um Volume, esse conteúdo é
perdido a cada novo deploy** (o container é recriado do zero). Para
persistir:

No serviço web → **Settings** → **Volumes** → **New Volume** → monte em
`/app/static/uploads`. Isso resolve para o TCC; para uma produção "de
verdade" o caminho recomendado é implementar um `StorageBackend` de nuvem
(S3, Cloudflare R2 etc.) em `backend/app/core/storage.py` — o resto do
código já foi desenhado para isso (só fala com a abstração, nunca com
disco diretamente).

### 8. Webhook do Mercado Pago

Depois do domínio gerado (passo 4), configure no painel do Mercado Pago
(aplicação de teste/produção) a URL de notificação:

```
https://seu-app.up.railway.app/api/v1/webhooks/mercadopago
```

e garanta que `MERCADO_PAGO_WEBHOOK_SECRET` no Railway é o mesmo secret
mostrado no painel do Mercado Pago (é ele que valida a assinatura HMAC —
ver `docs/frete-e-pagamento.md`).

## Observações / riscos conhecidos

- **Treinamento de ML não roda no serviço web.** `prophet`, `scikit-learn`
  etc. foram deixados de fora da imagem de produção (`requirements-web.txt`)
  porque só são usados pelo script offline `python -m app.ml.train`. Para
  gerar previsões em produção, rode esse script localmente (ou em qualquer
  máquina com Python) apontando `DATABASE_URL` para a Connection URL pública
  do Postgres do Railway — ele grava direto nas tabelas `ml_predictions` /
  `ml_model_metrics` / `restock_suggestions`, que é tudo que a API lê em
  runtime.
- **Custo**: Railway cobra por uso (CPU/RAM/rede) depois do free trial;
  Postgres + Redis + o serviço web juntos consomem mais que só o web
  sozinho. Para um TCC em demonstração, o plano Hobby geralmente é
  suficiente — vale checar os limites atuais em railway.app/pricing.
- **`SECRET_KEY` fraca**: o próprio código recusa subir (`RuntimeError`) se
  `ENVIRONMENT=production` e `SECRET_KEY` continuar no valor padrão do
  repositório — isso é intencional (ver `assert_production_safety` em
  `backend/app/core/config.py`), não um bug do deploy.
