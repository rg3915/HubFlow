# HubFlow

Gestão de projetos e fluxos de trabalho para quem desenvolve software para vários clientes.

Cada **cliente** é dono dos seus **projetos**; cada projeto corresponde a um **repositório** no GitHub ou no GitLab; o trabalho de cada projeto anda num **quadro kanban** com colunas fixas: Backlog → Sprint → Em desenvolvimento → QA → Concluído → Arquivadas. Tudo o que a interface faz também pode ser feito pela **API** e pela **CLI**.

## O que a aplicação faz

- **Login por e-mail** (sem username), com "esqueci minha senha" por e-mail e troca de senha.
- **Clientes** com lista de e-mails de notificação.
- **Projetos** ligados a um repositório (`github` ou `gitlab`, `owner/repo`), com e-mails próprios; sem e-mails, valem os do cliente.
- **Quadro kanban** por projeto: cards numerados por projeto (#1, #2…), arrastar e soltar entre colunas, reordenação, histórico de movimentações, arquivamento.
- **Sprints** numeradas por projeto (todo card pertence a uma; sem sprint informada usa a última aberta ou cria a primeira) e milestone opcional.
- **Controle de tempo**: cronômetro por card (um aberto por card; vários em cards diferentes), regra dos 15 minutos, lançamento manual de horas (só o dono apaga), estimativa com progresso gasto × estimado e exportação xlsx por período.
- **Quadro em tempo real**: quem mexer no quadro (tela, CLI ou webhook) atualiza a tela dos outros na hora (SSE + Redis), com indicador de quem está vendo.
- **Perfil** com avatar; cards mostram trecho da descrição e o dono.
- **Sincronização com GitHub/GitLab**: token por projeto, issue criada ao criar o card, edição e conclusão refletidas na issue, importação de issues existentes, milestone do repositório pareado com a sprint e webhooks (commit/PR com `close #N` conclui o card).
- **Dashboard** na página inicial: totais, cards por etapa, em desenvolvimento agora, cronômetros abertos, prazos, atividade recente, heatmap de horas (26 semanas), horas da semana por projeto e faturamento do mês.
- **Faturamento**: pagamentos por sprint ou por mês (valor/hora × horas registradas ou valor fechado), NF, emissão, pagamento, pendente/pago, resumo por cliente e por mês com gráficos.
- **Colaboração no card**: comentários com @menções (aviso por e-mail), etiquetas por projeto, prazo e responsável, checklist, anexos e histórico de atividade.
- **Notificações por e-mail** para uma ou mais pessoas, configuráveis por cliente e por projeto (card criado, movido, concluído).
- **Permissões**: papéis padrão (Administrador, Gerente, Desenvolvedor, Financeiro, Cliente, Leitura) com as permissões do Django, permissões extras por pessoa, vínculo pessoa ↔ cliente (quem não vê todos só enxerga os seus), uso da CLI e visibilidade de pagamentos controlados, convite por e-mail, histórico das alterações e tela de gestão de usuários.
- **Campos personalizados** por projeto (texto, número, data, seleção, sim/não, obrigatórios) no card, no quadro, na API e na CLI, e **formulário público** com link que cria card no Backlog sem login.
- **Automações** por projeto (quando o card for criado, entrar numa coluna ou estourar o SLA → mover, definir responsável, adicionar etiqueta ou avisar) e **SLA por coluna**, com verificação a cada 15 minutos e aviso de prazo vencido.
- **Notificações no app**: sino com menções, comentários e movimentações dos seus cards, e atalho "meus cards" com prazos.
- **Anexos** no disco ou num bucket S3 (AWS ou compatível).
- **API REST** (Django Ninja) com autenticação por token, documentada em `/api/docs`.
- **CLI `hubflow`** para criar clientes, projetos e cards, mover cards e iniciar tarefas por linha de comando.
- **Tema claro e escuro**.

O que vem a seguir está em [docs/especificacao.md](docs/especificacao.md) (notificações por e-mail, colaboração no card, sincronização GitHub/GitLab, tempo real, campos personalizados, automações, controle de tempo, relatórios).

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.14, Django 6.1 (ASGI/uvicorn), Django Ninja, Postgres 18, Redis |
| Frontend | Vue 3, Vite, Vue Router, Pinia, Tailwind 4, SortableJS |
| CLI | Python, Typer, httpx |
| E-mail (dev) | Mailpit |
| Infra | Docker Compose, uv |

## Instalação

Pré-requisitos: Docker e Docker Compose.

```bash
git clone https://github.com/rg3915/HubFlow.git
cd HubFlow
cp .env.example .env
docker compose up --build
```

Em outro terminal, crie as tabelas e o primeiro usuário:

```bash
docker compose exec backend uv run python manage.py migrate
docker compose exec backend uv run python manage.py createsuperuser
```

| Serviço | Endereço |
|---|---|
| Aplicação | http://localhost:5173 |
| API e documentação | http://localhost:8000/api/docs |
| Admin do Django | http://localhost:8000/admin/ |
| Mailpit (e-mails enviados) | http://localhost:8025 |
| Redis (tempo real) | localhost:6379 |

O `.env.example` já aponta para os serviços do compose. As variáveis que importam: `SECRET_KEY`, `DEBUG`, `DATABASE_URL`, `EMAIL_HOST`/`EMAIL_PORT`, `FRONTEND_URL` (usado nos links dos e-mails) e `VITE_API_URL`.

### Agendador

O serviço `scheduler` do compose roda, a cada 15 minutos, `python manage.py check_sla` (automações de SLA estourado e aviso de prazos vencidos) e `python manage.py send_reports` (relatórios agendados dos períodos encerrados). Fora do Docker, agende o mesmo comando (cron, por exemplo).

### Anexos no S3 ou no Cloudinary (opcional)

Por padrão os anexos e avatares ficam no disco (volume `media`). Para guardar num bucket S3 (AWS ou compatível), defina `STORAGE_BACKEND=s3` e as variáveis `AWS_*` do `.env.example`. Em desenvolvimento há um S3 local (SeaweedFS) no perfil `s3`, já com o bucket criado:

```bash
docker compose --profile s3 up -d      # S3 em http://localhost:8333, bucket "hubflow"
# no .env: STORAGE_BACKEND=s3 (os demais AWS_* do .env.example já apontam para ele)
docker compose restart backend
```

Na AWS, deixe `AWS_S3_ENDPOINT_URL` e `AWS_S3_CUSTOM_DOMAIN` vazios: os links dos arquivos saem assinados.

No Cloudinary: `STORAGE_BACKEND=cloudinary` e `CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD_NAME` (copie do painel do Cloudinary). Os arquivos sobem como "raw", com nome único.

### Rodando fora do Docker

Backend (precisa de um Postgres em `localhost:5432`, por exemplo `docker compose up -d db mailpit`):

```bash
cd backend
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Primeiros passos

1. Entre em http://localhost:5173 com o e-mail e a senha do superusuário.
2. Crie um cliente (barra lateral → **Novo cliente**).
3. Crie um projeto para o cliente informando provedor, owner e repositório.
4. Abra o projeto: o quadro aparece com as seis colunas. Use **Novo card** no Backlog e arraste os cards entre as colunas.

## E-mails

Em desenvolvimento, nenhum e-mail sai para a internet: tudo cai no Mailpit (http://localhost:8025). É lá que você abre o link de "esqueci minha senha".

## API

Todas as rotas, exceto login e redefinição de senha, exigem o cabeçalho `Authorization: Bearer <token>`.

```bash
# login
curl -X POST localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email": "voce@hubflow.com", "password": "sua-senha"}'
# → {"token": "..."}

# clientes e projetos
curl -H "Authorization: Bearer $TOKEN" localhost:8000/api/clients
curl -H "Authorization: Bearer $TOKEN" localhost:8000/api/projects?client=1

# quadro e cards
curl -H "Authorization: Bearer $TOKEN" localhost:8000/api/projects/1/board
curl -X POST -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  localhost:8000/api/projects/1/cards -d '{"title": "Corrigir login"}'
curl -X POST -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  localhost:8000/api/cards/1/move -d '{"column": "qa", "position": 0}'
```

| Rota | O que faz |
|---|---|
| `POST /api/auth/login`, `/logout`, `GET /api/auth/me` | Sessão por token |
| `POST /api/auth/password/forgot`, `/reset`, `/change` | Senha |
| `GET/POST /api/clients`, `GET/PUT/DELETE /api/clients/{id}` | Clientes |
| `GET/POST /api/projects`, `GET/PUT/DELETE /api/projects/{id}` | Projetos (`?client=` filtra) |
| `POST /api/projects/full` | Cliente + projeto + sprint 1 (+ milestone) numa chamada |
| `GET/POST /api/projects/{id}/sprints`, `.../sprints/current`, `PUT /api/sprints/{id}`, `POST .../close` | Sprints |
| `GET/POST /api/projects/{id}/milestones`, `POST /api/milestones/{id}/close` | Milestones |
| `GET /api/projects/{id}/board` | Quadro (`?archived=true` inclui Arquivadas, `?sprint=` filtra) |
| `POST /api/projects/{id}/cards` | Cria card no Backlog |
| `GET/PUT/DELETE /api/cards/{id}` | Card |
| `POST /api/cards/{id}/move`, `/start`, `/archive` | Move, inicia (Em desenvolvimento), arquiva |
| `GET /api/cards/{id}/history`, `/activity` | Movimentações e linha do tempo completa |
| `GET/POST /api/cards/{id}/comments`, `PUT/DELETE /api/comments/{id}` | Comentários (com @menções) |
| `GET/POST /api/projects/{id}/labels`, `PUT/DELETE /api/labels/{id}`, `PUT /api/cards/{id}/labels` | Etiquetas |
| `GET/POST /api/cards/{id}/checklist`, `PUT/DELETE /api/checklist/{id}`, `PUT .../checklist/order` | Checklist |
| `GET/POST /api/cards/{id}/attachments`, `DELETE /api/attachments/{id}` | Anexos |
| `POST /api/cards/{id}/timer/start`, `/timer/stop`, `GET /api/cards/{id}/time` | Cronômetro e tempo do card |
| `POST /api/cards/{id}/time-entries`, `PUT/DELETE /api/time-entries/{id}` | Horas manuais (só o dono edita/apaga) |
| `GET /api/projects/{id}/timesheet.xlsx?from=&to=` | Exportação xlsx do timesheet |
| `GET/POST /api/payments`, `GET/PUT/DELETE /api/payments/{id}`, `POST .../pay`, `.../copy`, `GET /api/payments/summary` | Faturamento |
| `GET/PUT /api/projects/{id}/repo`, `POST .../repo/check`, `POST .../import-issues` | Integração com o repositório |
| `POST /api/webhooks/github/{id}`, `/api/webhooks/gitlab/{id}` | Webhooks (sem token; assinatura/segredo) |
| `GET /api/projects/{id}/events?token=` (SSE), `GET/POST/DELETE /api/projects/{id}/presence` | Tempo real e presença |
| `POST/DELETE /api/auth/me/avatar` | Avatar do usuário |
| `GET /api/dashboard`, `/activity`, `/deadlines`, `/heatmap`, `/week`, `/billing` | Dashboard |
| `GET /api/users` | Usuários ativos (responsáveis e menções) |

A documentação interativa fica em http://localhost:8000/api/docs.

## CLI

Instale a partir da pasta `cli/`:

```bash
uv tool install ./cli        # ou: pipx install ./cli
hubflow --help
```

Só quem tem a permissão **Usar a CLI** (papéis Administrador, Gerente e Desenvolvedor por padrão) consegue entrar pela CLI.

```bash
hubflow login                                   # pede e-mail e senha; guarda o token em ~/.config/hubflow/config.toml
hubflow whoami
hubflow logout

hubflow client create "ACME" --emails ti@hubflow.com
hubflow client list

hubflow project create "Loja" --client ACME --provider github --repo acme/loja
hubflow project create "Loja" --client ACME --provider github --repo acme/loja --full --milestone v1.0   # cria cliente + sprint 1
hubflow project list [--client ACME]
hubflow project notify Loja --off moved         # liga/desliga os avisos: created, moved, done
hubflow project emails Loja --set dev@hubflow.com  # quem recebe; vazio = e-mails do cliente

hubflow sprint create --project Loja --name "Checkout" --start 2026-10-13
hubflow sprint list --project Loja
hubflow sprint close 1 --project Loja

hubflow card create "Corrigir login" --project Loja --description "Erro 500"   # pergunta se quer criar uma sprint nova
hubflow card create "Corrigir login" --project Loja --sprint 2                  # ou --no-input para usar a última aberta
hubflow card list --project Loja [--column doing]
hubflow card move 3 --project Loja --to qa [--position 0]
hubflow card start 3 --project Loja              # move para Em desenvolvimento
hubflow card comment 3 --project Loja "Pronto para QA, @bruno@hubflow.com"
hubflow card label 3 --project Loja --add bug --remove ui
hubflow card assign 3 --project Loja --to bruno@hubflow.com   # ou --clear
hubflow card due 3 --project Loja 2026-10-20                  # ou "nenhum"

hubflow card start 3 --project Loja          # move para Em desenvolvimento e abre o cronômetro
hubflow card stop 3 --project Loja           # fecha o cronômetro (mostra sessão e total)
hubflow card log 3 --project Loja --hours 1.5 --date 2026-10-13 --note "Reunião"
hubflow card time 3 --project Loja           # entradas e total do card
hubflow timesheets --project Loja --limit 10 # últimas entradas

hubflow payment create --project Loja --month 2026-10 --rate 150     # ou --sprint 2; --hours, --fixed, --invoice, --issue-date
hubflow payment list [--client ACME] [--status pending|paid] [--year 2026]
hubflow payment pay 1 / hubflow payment copy 1
hubflow payment summary [--client ACME] [--year 2026]

hubflow project field add Loja Prioridade --kind select --option Alta --option Baixa [--required]
hubflow project field list Loja / hubflow project field remove Loja Prioridade
hubflow card create "Login" --project Loja --field Prioridade=Alta --field Pontos=3
hubflow card fields 12 --project Loja [--field Prioridade=Baixa]

hubflow automation add "QA aprovado" --project Loja --when entered:qa --then move:done
hubflow automation list --project Loja / hubflow automation toggle 1 --project Loja / hubflow automation remove 1
hubflow project sla Loja [--column qa --hours 48 | --column qa --clear]

hubflow user list                                                     # só quem gerencia usuários
hubflow user invite ana@hubflow.com --name Ana --role Desenvolvedor --client ACME
hubflow user role ana@hubflow.com --set Gerente [--set Financeiro]
hubflow user grant ana@hubflow.com --perm billing.view_payment [--revoke]

hubflow project repo Loja --token ghp_xxx --create-issues --webhook-secret abc   # integração com o repositório
hubflow project repo-check Loja
hubflow project import-issues Loja [--include-closed]
```

Variáveis de ambiente: `HUBFLOW_URL` (padrão `http://localhost:8000`) e `HUBFLOW_TOKEN` (sobrescreve o arquivo de configuração).

## Testes

Backend (modelos, autenticação e todos os endpoints) e CLI (com a API simulada):

```bash
docker compose exec backend uv run pytest      # ou: cd backend && uv run pytest
cd cli && uv run pytest
```

Os testes do backend usam o Postgres do compose. O frontend ainda não tem testes automatizados.

### Atalhos (taskipy)

```bash
cd backend
uv run task test             # suíte do backend
uv run task lint             # ruff check --fix + ruff format
uv run task makemigrations   # gera migrations
uv run task migrate          # aplica as migrations no container
uv run task sync             # instala dependências novas no container e reinicia o backend

cd cli
uv run task test
uv run task lint
```

`uv run task --list` mostra todos.

No macOS, o PDF dos relatórios (WeasyPrint) precisa do pango: `brew install pango`. O `task test` já aponta para as bibliotecas do Homebrew; rodando `pytest` direto, exporte `DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib`.

## Documentação

- [docs/especificacao.md](docs/especificacao.md): conceitos, entregáveis, endpoints e CLI.
- [docs/regras-de-negocio.md](docs/regras-de-negocio.md): regras numeradas (RN-01…), citadas nos testes.
- [docs/arquitetura.md](docs/arquitetura.md): estrutura das pastas e decisões.
- [docs/design.md](docs/design.md): princípios visuais, paleta e tipografia.
- [CHANGELOG.md](CHANGELOG.md): o que mudou em cada versão.
