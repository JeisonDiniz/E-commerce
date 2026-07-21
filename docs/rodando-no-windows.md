# Rodando o projeto no Windows (PowerShell)

Guia passo a passo assumindo que você **não tem Postgres/Redis instalados**
ainda. Vamos usar Docker Desktop só para o banco e o cache — o back-end e o
front-end continuam rodando direto no Windows (mais fácil de depurar).

## 0. Pré-requisitos (uma vez só)

1. **Docker Desktop** — baixe em https://www.docker.com/products/docker-desktop/
   e instale. Na primeira execução ele pode pedir para habilitar o WSL2 e
   reiniciar o Windows — aceite. Depois de instalado, abra o Docker Desktop
   e espere o ícone da baleia ficar "Running" (verde) na bandeja do sistema.
2. **Python 3.13** — https://www.python.org/downloads/ (marque a opção "Add
   python.exe to PATH" no instalador).
3. **Node.js 20 LTS** — https://nodejs.org/

Verifique no PowerShell:

```powershell
docker --version
python --version
node --version
```

## 1. Subir Postgres e Redis

Na raiz do projeto (`c:\Users\marinho\Desktop\E-commerce`):

```powershell
docker compose up -d
```

Isso baixa as imagens do Postgres 16 e Redis 7 (só na primeira vez, pode
demorar alguns minutos) e sobe os dois containers em segundo plano. Confira:

```powershell
docker compose ps
```

Ambos devem aparecer com status `running` (o Postgres pode levar ~10s a mais
para ficar `healthy`).

## 2. Criar as tabelas do banco

```powershell
docker compose exec postgres psql -U postgres -d ecommerce_ml -f /database/schema.sql
```

Se aparecer uma lista de `CREATE TABLE`, `CREATE TYPE`, etc. sem erros, deu certo.

## 3. Back-end (FastAPI)

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
```

> Se o PowerShell bloquear com um erro de "execution policy", rode uma vez
> (só nessa sessão do terminal, não precisa mexer em configuração global):
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> ```
> e tente `.venv\Scripts\Activate.ps1` de novo.

Com o venv ativado (o prompt passa a mostrar `(.venv)` na frente):

```powershell
pip install -r requirements.txt
Copy-Item .env.example .env
```

Os valores padrão do `.env` já apontam para `localhost:5432` (Postgres) e
`localhost:6379` (Redis) — exatamente o que o `docker compose up -d` subiu,
então não precisa editar nada.

```powershell
python -m scripts.seed_database
python -m app.ml.train --source db
uvicorn app.main:app --reload
```

Deixe esse terminal aberto rodando o `uvicorn`. Acesse
http://localhost:8000/docs para ver a documentação interativa da API.

## 4. Front-end (React)

Abra **um novo terminal do PowerShell** (não feche o do back-end):

```powershell
cd c:\Users\marinho\Desktop\E-commerce\frontend
npm install
npm run dev
```

Acesse http://localhost:5173.

## 5. Testando

- Loja: navegue pelo catálogo sem estar logado, crie uma conta em "Cadastre-se", adicione um produto ao carrinho e finalize a compra.
- Painel admin: faça login com `gestor@loja.com` / senha `Senha@123` e acesse http://localhost:5173/admin — deve mostrar o dashboard com gráficos de vendas e a previsão de tendência por categoria.

## Problemas comuns

| Sintoma | Causa provável | Solução |
|---|---|---|
| `docker compose up` trava ou dá erro de conexão | Docker Desktop não terminou de iniciar | Espere o ícone da baleia ficar verde e tente de novo |
| Erro de "execution policy" ao ativar o venv | Política de execução do PowerShell bloqueia scripts | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` (só nessa sessão) |
| `psql: command not found` fora do Docker | Você tentou rodar `psql` direto no Windows | Use sempre `docker compose exec postgres psql ...` (o cliente psql já está dentro do container) |
| Porta 5432 ou 6379 já em uso | Outro serviço (ex: Postgres nativo já instalado) usando a porta | Pare o outro serviço, ou edite as portas em `docker-compose.yml` (e o `.env` do back-end) |
| Dashboard mostra "Nenhuma previsão disponível ainda" | O treinamento de ML ainda não rodou | Rode `python -m app.ml.train --source db` no back-end |