# Build único (front + back) para deploy em produção (ex.: Railway) num só
# serviço. Builda o React (Vite) e serve o resultado estático pelo próprio
# FastAPI (ver bloco "Front-end" no fim de backend/app/main.py) — assim
# front e back ficam no mesmo domínio, sem CORS e sem URLs relativas
# quebrando (ex.: imagens em /media, chamadas em /api/v1).
#
# Localmente continue rodando front (`npm run dev`, porta 5173) e back
# (`uvicorn --reload`, porta 8000) separados — este Dockerfile é só para
# deploy. Contexto de build = raiz do repositório.

# ---- Etapa 1: build do front-end ----
FROM node:20-slim AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# ---- Etapa 2: back-end (FastAPI) + front-end já buildado ----
FROM python:3.13-slim
WORKDIR /app

# build-essential cobre o caso raro de alguma dependência (bcrypt,
# cryptography) não ter wheel pronta para a plataforma de build.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# requirements-web.txt = requirements.txt sem as libs de ML (pandas, numpy,
# scikit-learn, prophet, joblib), que só são usadas pelo treinamento
# offline (`python -m app.ml.train`), nunca pela API em produção — ver
# comentário em backend/requirements-web.txt. Isso mantém o build rápido e
# evita a compilação pesada do CmdStan (prophet) na imagem de produção.
COPY backend/requirements-web.txt .
RUN pip install --no-cache-dir -r requirements-web.txt

COPY backend/ .
COPY --from=frontend-build /frontend/dist ./frontend_dist

# MEDIA_ROOT (uploads de imagem) — ver app/core/storage.py. Sem um volume
# do Railway montado aqui, o conteúdo é perdido a cada novo deploy.
RUN mkdir -p static/uploads

EXPOSE 8000

# $PORT é injetado pelo Railway; 8000 é o fallback para `docker run` local.
# Forma exec chamando "sh -c" (em vez de forma shell implícita) para o
# Docker propagar SIGTERM corretamente ao uvicorn, mantendo a expansão da
# variável de ambiente.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
