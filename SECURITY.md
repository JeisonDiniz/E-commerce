# Segurança da aplicação

Nenhum sistema é 100% invulnerável — o objetivo aqui é eliminar as classes
de falha mais comuns e documentar honestamente o que ainda depende de como
o projeto é hospedado/operado. Este documento resume o que já está
implementado e o que fica a cargo do ambiente de deploy.

## Já implementado no código

- **Sem SQL injection**: todo acesso a dados passa pelo SQLAlchemy ORM com
  parâmetros ligados (bind parameters) — nunca há montagem de SQL por
  concatenação de string.
- **Senhas com bcrypt** (`passlib`), nunca em texto puro.
- **Autenticação por JWT** (Bearer token), assinado com `SECRET_KEY`.
- **RBAC** (`require_roles`): endpoints de estoque, produtos, relatórios e
  pedidos exigem papel staff/manager/admin explicitamente.
- **Sem escalonamento de privilégio no cadastro**: `POST /auth/register`
  sempre cria a conta como `customer`; o campo `role` não existe mais no
  payload aceito pelo cliente. Contas staff/manager/admin só são criadas via
  `backend/scripts/seed_database.py` ou diretamente no banco.
- **Rate limiting de login e "esqueci minha senha"** via Redis (contador por
  e-mail+IP), para dificultar força bruta e abuso de envio de e-mail.
- **Reset de senha seguro**: token aleatório de 256 bits, guardado só como
  hash SHA-256, de uso único e com expiração; resposta sempre genérica
  (não revela se o e-mail existe).
- **Sem IDOR conhecido**: carrinho, endereços e pedidos são sempre
  filtrados pelo usuário autenticado (`current_user.id`); nunca por um ID
  vindo do cliente sem checagem de posse.
- **Upload de imagem validado**: tipo de conteúdo restrito
  (JPEG/PNG/WEBP), limite de tamanho, decodificação real com Pillow
  (rejeita arquivos disfarçados de imagem) e nome de arquivo sempre gerado
  no servidor (nunca o nome enviado pelo cliente) — evita path traversal e
  upload de executáveis/scripts disfarçados.
- **Headers de segurança HTTP** em toda resposta: `X-Content-Type-Options`,
  `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, e
  `Strict-Transport-Security` quando servido via HTTPS.
- **CORS restrito** a uma allowlist de origens configurável, com métodos e
  headers explícitos (não `*`).
- **Guarda de ambiente**: o back-end recusa subir com `ENVIRONMENT=production`
  se `SECRET_KEY` ainda for o valor padrão do repositório.

## Responsabilidade do ambiente de deploy (fora do código)

Estas ações não são gerenciáveis pela aplicação sozinha — devem ser feitas
na hora de colocar o site no ar:

- **HTTPS obrigatório**: sirva a API e o front-end atrás de um proxy
  reverso (nginx/Caddy/Cloudflare) com certificado TLS válido; nunca exponha
  a API diretamente em HTTP na internet.
- **`SECRET_KEY` forte e secreta**: gere um valor aleatório longo
  (ex.: `openssl rand -hex 32`) e nunca o versione no Git.
- **Backups regulares** do banco Postgres.
- **Firewall/rede**: Postgres e Redis não devem ficar expostos publicamente
  — só acessíveis pela própria API.
- **Dependências em dia**: rode periodicamente `pip list --outdated` /
  `npm audit` e atualize bibliotecas com vulnerabilidades conhecidas.
- **Armazenamento de imagens em produção**: `STORAGE_BACKEND=local` é
  adequado para desenvolvimento; num deploy real, prefira um backend
  externo (implementando uma nova classe em `backend/app/core/storage.py`)
  para não depender do disco de uma única instância.
