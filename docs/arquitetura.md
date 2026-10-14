# HubFlow — Arquitetura

```
HubFlow/
├── compose.yaml            # Postgres 18, Mailpit, backend, frontend
├── .env.example
├── backend/                # Django 6.1.2 + Django Ninja
│   ├── Dockerfile
│   ├── pyproject.toml      # uv
│   ├── manage.py
│   └── hubflow/
│       ├── settings.py     # tudo via variáveis de ambiente
│       ├── urls.py
│       ├── api.py          # NinjaAPI: junta os routers dos apps
│       ├── accounts/       # User (e-mail), tokens, redefinição de senha
│       ├── clients/        # Cliente
│       ├── projects/       # Projeto
│       └── boards/         # Card, colunas, movimentações
├── cli/                    # pacote `hubflow` (Typer + httpx)
│   ├── pyproject.toml
│   └── hubflow_cli/
├── frontend/               # Vue 3 + Vite + Tailwind 4
│   ├── Dockerfile
│   └── src/
└── docs/
```

## Decisões

- **Apps por domínio** (`accounts`, `clients`, `projects`, `boards`), cada um com `models.py`, `api.py` (router do Ninja), `schemas.py` e `tests/`.
- **Autenticação por token** em tabela própria (`accounts.Token`), um por sessão/dispositivo. Simples, serve ao SPA e à CLI, e permite revogar um só. Sem JWT: não há ganho aqui e complica o logout.
- **CLI separada do backend**: é instalável com `uv tool install ./cli` ou `pipx` em qualquer máquina e só precisa da URL da API.
- **Frontend servido pelo Vite em dev** (porta 5173) chamando a API em `localhost:8000`. CORS liberado só para essa origem em dev.
- **Postgres desde o primeiro dia** (nada de SQLite em dev) para que os testes rodem no mesmo banco da produção. Os testes usam o Postgres do compose.
- **Mailpit** recebe todos os e-mails em dev. `EMAIL_HOST=mailpit`, porta 1025.

## Serviços do compose

| Serviço | Imagem | Porta |
|---|---|---|
| `db` | `postgres:18` | 5432 |
| `mailpit` | `axllent/mailpit` | 1025 (SMTP), 8025 (web) |
| `backend` | build `./backend` | 8000 |
| `frontend` | build `./frontend` | 5173 |

## Como rodar

```bash
cp .env.example .env
docker compose up --build
docker compose exec backend uv run python manage.py migrate
docker compose exec backend uv run python manage.py createsuperuser
```

Testes:

```bash
docker compose exec backend uv run pytest
cd cli && uv run pytest
```
