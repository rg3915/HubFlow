# HubFlow — Especificação

HubFlow é um gestor de projetos e fluxos de trabalho para quem desenvolve software para vários clientes. Cada cliente é dono dos seus projetos; cada projeto corresponde a um repositório (GitHub ou GitLab); o trabalho de cada projeto anda num quadro kanban com colunas fixas. Tudo o que a interface faz também pode ser feito pela API e pela CLI.

## Visão geral

| Conceito | Descrição |
|---|---|
| **Usuário** | Pessoa que entra no sistema. Identificada pelo e-mail (não há username). |
| **Cliente** | Dono de um ou mais projetos. Pode ter uma lista de e-mails para notificação. |
| **Projeto** | Um repositório. Pertence a um cliente. Tem provedor (`github` ou `gitlab`), `owner` e `repo`. Pode ter sua própria lista de e-mails. |
| **Card** | Unidade de trabalho dentro de um projeto (issue, tarefa, bug). Está sempre em uma coluna e tem uma posição dentro dela. |
| **Coluna** | Uma das seis etapas fixas: `backlog`, `sprint`, `doing` (Em desenvolvimento), `qa`, `done` (Concluído), `archived` (Arquivadas). |

## Entregáveis

Cada entregável é um milestone no GitHub. A versão do CHANGELOG avança a cada entregável concluído. As trilhas 1.0 (essencial) e 2.0 (integrações e automação) foram propostas em 13/10/26; a numeração 0.x segue até fechar o essencial.

| # | Entregável | Versão | Situação |
|---|---|---|---|
| 1 | Base e login por e-mail | 0.1.0 | concluído |
| 2 | Clientes e projetos | 0.1.0 | concluído |
| 3 | Quadro kanban | 0.1.0 | concluído |
| 4 | Notificações por e-mail | 0.2.0 | concluído |
| 5 | Colaboração no card | 0.3.0 | em andamento |
| 13 | Sprints e milestones | 0.4.0 | |
| 9 | Controle de tempo (cronômetro, horas manuais, estimativa, xlsx) | 0.5.0 | |
| 14 | Faturamento por sprint | 0.6.0 | |
| 15 | Dashboard | 0.7.0 | |
| 6 | Sincronização GitHub/GitLab (tokens por projeto, issues, importação, milestones, webhooks) | 0.8.0 | |
| 12 | Quadro em tempo real | 0.9.0 | |
| 7 | Campos personalizados e formulários | 0.12.0 | concluído |
| 8 | Automações e SLA | 0.13.0 | concluído |
| 10 | Relatórios e métricas (PDF por período, envio por e-mail) | 1.x | a definir |
| 17 | Permissões (papéis, permissões por pessoa, clientes vinculados, CLI, pagamentos, tela de gestão) | 0.10.0 | concluído |
| 11 | Polimento: busca global, notificações no app, backup .sql, S3, taskipy | 0.10.0 / 0.11.0 | concluído |
| 16 | Mobile (2.5): layout responsivo | 2.5 | extra no final |

Fora do escopo (decidido em 13/10/26): Pipefy, GitHub Projects v2, Bitbucket, prefixo de título por projeto, geração de tarefas.txt/commit/changelog a partir do card, app de barra de menu, matriz de horas e heatmap fora do dashboard.

## Stack

- Backend: Python 3.14, Django 6.1.2, Django Ninja, Postgres 18.
- Frontend: Vue 3, Vite, Vue Router, Pinia, Tailwind 4. Tema claro e escuro, sem neon.
- E-mail: Mailpit em desenvolvimento (SMTP na porta 1025, interface web na 8025).
- CLI: pacote Python `hubflow` (Typer + httpx) que fala com a API.
- Infra: Docker Compose sobe tudo com um comando.

## Autenticação

- Login por **e-mail e senha**. Não existe username.
- A API responde com um **token** (Bearer) que o frontend e a CLI guardam.
- Fluxo "esqueci minha senha": o usuário informa o e-mail; recebe um link com token de uso único; define a nova senha. Em desenvolvimento o e-mail aparece no Mailpit.
- Usuário logado pode trocar a própria senha informando a atual.

### Endpoints

| Método | Rota | O que faz |
|---|---|---|
| POST | `/api/auth/login` | `{email, password}` → `{token}` |
| POST | `/api/auth/logout` | Invalida o token atual |
| GET | `/api/auth/me` | Dados do usuário logado |
| POST | `/api/auth/password/forgot` | `{email}` → envia e-mail (sempre 200, mesmo se o e-mail não existir) |
| POST | `/api/auth/password/reset` | `{uid, token, password}` → define a nova senha |
| POST | `/api/auth/password/change` | `{current_password, new_password}` (logado) |

## Clientes e projetos

| Método | Rota |
|---|---|
| GET / POST | `/api/clients` |
| GET / PUT / DELETE | `/api/clients/{id}` |
| GET / POST | `/api/projects` (filtro `?client=`) |
| GET / PUT / DELETE | `/api/projects/{id}` |

Projeto: `{client, name, provider, owner, repo, description}`. `provider` ∈ `github|gitlab`. A URL do repositório é derivada: `https://github.com/{owner}/{repo}` ou `https://gitlab.com/{owner}/{repo}`.

## Quadro e cards

| Método | Rota | O que faz |
|---|---|---|
| GET | `/api/projects/{id}/board` | Colunas com os cards ordenados por posição |
| POST | `/api/projects/{id}/cards` | Cria card (vai para o backlog, última posição) |
| GET / PUT / DELETE | `/api/cards/{id}` | |
| POST | `/api/cards/{id}/move` | `{column, position?}` → move e reordena |
| POST | `/api/cards/{id}/start` | Atalho: move para `doing` |

Card: `{project, title, description, column, position, number}`. `number` é sequencial por projeto (como o número da issue).

## CLI

```
hubflow login                         # pede e-mail e senha, guarda o token em ~/.config/hubflow/config.toml
hubflow logout
hubflow whoami

hubflow client create "ACME"
hubflow client list

hubflow project create "Loja" --client ACME --provider github --repo acme/loja
hubflow project list [--client ACME]

hubflow card create "Corrigir login" --project Loja [--description "..."]
hubflow card list --project Loja [--column sprint]
hubflow card move 12 --to qa [--position 0]
hubflow card start 12
```

Variáveis: `HUBFLOW_URL` (padrão `http://localhost:8000`), `HUBFLOW_TOKEN` (sobrescreve o arquivo de configuração).

## Testes

- Backend: `pytest` + `pytest-django`. Testes de modelos, autenticação e de cada endpoint da API.
- CLI: `pytest` com a API simulada por `respx`; cada comando tem teste.
- Frontend: sem testes por enquanto.

Os testes são escritos **antes** da implementação (TDD).
