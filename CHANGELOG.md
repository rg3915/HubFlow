# Changelog

Todas as mudanças relevantes deste projeto são registradas aqui.

O formato segue o [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o projeto usa [versionamento semântico](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Adicionado

* Model de automação por projeto (app automations): gatilho (card criado, entrou na coluna, SLA estourado) → ação (mover, definir responsável, adicionar etiqueta, avisar), com validação e descrição em linguagem simples. #148
* Motor das automações: roda as regras ligadas ao criar e ao mover card (API, CLI, webhooks), sem laço (ação de automação não dispara outra), registra no histórico e avisa no sino. #149
* API de automações: listar, criar, editar (inclusive ligar/desligar) e excluir, com a descrição da regra (projects.change_project para alterar). #150
* SLA por coluna: horas máximas por coluna do projeto (GET/PUT /api/projects/{id}/sla); o card guarda quando entrou na coluna e informa o SLA (prazo e se estourou) no quadro e na API. #151

### Alterado

* Refactor: schemas de saída da API com ModelSchema (campos vindos do model; *_id, propriedades e calculados continuam declarados) e um só schema resumido de sprint; respostas iguais. #147

### Corrigido

* Quadro sem N+1: horas gastas, cronômetro aberto, contagem de anexos e sprint vêm na mesma consulta dos cards. #151

## [0.12.0] - 2026-10-14

Campos personalizados por projeto (no card, no quadro, na API e na CLI), formulário público que cria card sem login e anexos no Cloudinary.

### Adicionado

#### Campos personalizados e formulários

* Model de campo personalizado por projeto: nome (único no projeto), tipo (texto, número, data, seleção, sim/não), opções, obrigatório e ordem. #136
* API de campos personalizados: listar, criar, editar, excluir e reordenar (projects.change_project para alterar). #137
* Valores dos campos personalizados no card (`fields` na criação/edição, `custom_values` na resposta): validação por tipo, opção da seleção, obrigatórios ao criar e não podem ser esvaziados; mudanças entram no histórico. #138
* CLI: hubflow project field list/add/remove, card create --field Nome=valor e card fields (mostra/altera). #139
* Tela de campos do projeto (Quadro › Campos): criar, editar tipo/opções/obrigatório, reordenar e excluir. #140
* Campos no painel do card (entrada conforme o tipo, obrigatórios marcados, salva só o que mudou), obrigatórios pedidos no "Novo card", até dois valores no card do quadro e mudanças de campos no histórico. #141
* Formulário público do projeto: link com token (ligar/desligar, gerar outro) que cria card no Backlog sem login, com título, descrição, contato e campos; limite de envios por IP (FORM_SUBMISSIONS_PER_HOUR). #142
* Tela do formulário público (/form/TOKEN, sem login, com confirmação do card criado) e configuração na tela de campos: ligar, copiar, abrir e gerar outro link. #143
* CHANGELOG 0.12.0; README e regras RN-100 e RN-101. #144

#### Polimento

* Anexos e avatares no Cloudinary (STORAGE_BACKEND=cloudinary e CLOUDINARY_URL) com a lib oficial do Cloudinary. #145

### Corrigido

* CLI: card label/assign/due não apagam mais a estimativa do card. #139
* Quadro: mudar etiquetas/responsável pelo painel não apaga mais a estimativa do card. #141

## [0.11.0] - 2026-10-14

Polimento: notificações no app (sino), meus cards, anexos no S3, atalhos com taskipy e uuid7 em todos os models.

### Adicionado

* Notificações no app: menção, comentário em card seu ou de que é responsável e card seu movido por outra pessoa (sem duplicar, sem avisar quem fez); GET /api/notifications (não lidas primeiro + total), POST /api/notifications/{id}/read e /read-all. #114
* API meus cards: GET /api/me/cards com os cards em aberto sob sua responsabilidade (projeto, cliente, coluna, prazo), vencidos primeiro. #116
* Cabeçalho com sino (contador de não lidas, lista, marcar todas; abrir a notificação marca como lida e abre o card) e meus cards (contador e lista com prazo/vencidos), atualizados a cada minuto e a cada troca de página. #115
* Anexos e avatares no S3 (AWS ou compatível) via django-storages com STORAGE_BACKEND=s3; S3 local (SeaweedFS) no perfil `s3` do compose com o bucket criado automaticamente; frontend aceita URL absoluta dos arquivos. #113
* Atalhos de desenvolvimento com taskipy (backend: test, lint, makemigrations, migrate, sync; CLI: test, lint). #135

### Alterado

* Refactor: UuidModel (uuid7, campo `uuid` único além do id) em todos os models e só TimeStampedModel (created/modified) no lugar de CreatedModel; User.date_joined vira created; a API expõe o uuid. #134

## [0.10.0] - 2026-10-14

Permissões: papéis padrão, permissões por pessoa, escopo por cliente, uso da CLI, visibilidade de pagamentos, convite por e-mail, histórico e tela de gestão de usuários. Também busca global e backup .sql.

### Adicionado

#### Permissões

* Permissões: permissões padrão do Django (view/add/change/delete) + use_cli e view_own_payments, papéis padrão (Administrador, Gerente, Desenvolvedor, Financeiro, Cliente, Leitura) e vínculo usuário↔cliente. #118
* API de usuários, papéis e permissões (só quem gerencia usuários): listar, papéis, permissões por pessoa, clientes, ativar/desativar; /api/auth/me devolve papéis e permissões efetivas. #119
* Permissões em clientes e projetos: sem clients.view_client só vê os clientes de que é membro; criar/editar/excluir exige as permissões padrão (403 com a permissão nomeada). #120
* Permissões em cards e comentários: add_card para criar; sem change_card/delete_card só edita, move, exclui e arquiva os próprios (criado por ou responsável); delete_comment para apagar comentários de outros. #121
* Permissões em sprints, milestones, etiquetas e anexos: add/change/delete de sprint, milestone e etiqueta exigem as permissões padrão; sprint/etiqueta de cliente de fora dá 404; anexar e excluir anexo seguem a regra do card (quem enviou ou quem pode editar o card). #122
* Permissão de uso da CLI: a CLI se identifica com X-HubFlow-Client: cli; o login pela CLI exige permissions.use_cli (403 com o motivo) e marca o token (is_cli), que deixa de valer se a permissão for retirada. #123
* Permissões de pagamentos: billing.view_payment vê todos, view_own_payments só os dos clientes de que é membro (lista, detalhe, resumo e faturamento do dashboard), sem nenhuma 403; criar, editar/pagar/copiar e excluir exigem add/change/delete_payment. #124
* Convite por e-mail: POST /api/users/invite (accounts.add_user) cria a pessoa sem senha, com papéis e clientes, e envia o link para definir a senha (mesmo fluxo da redefinição). #125
* Registro de alterações de permissões: convite, papéis, permissões por pessoa, clientes vinculados e situação guardam quem fez, quando, o antes e o depois; GET /api/users/changes (filtro ?user=) e admin. #126
* Frontend respeita as permissões de /api/auth/me: menu, rotas, botões de criar/editar/excluir (clientes, projetos, cards, sprints, etiquetas, pagamentos), arrastar só os cards que a pessoa pode mover, painel do card só leitura para quem não pode editar. #127
* Tela de usuários e permissões (/settings/users): lista com papéis, clientes e situação; painel com papéis, clientes vinculados, CLI sim/não, pagamentos (todos / só os seus / nenhum), permissões por pessoa (travadas as que vêm do papel), ativar/desativar, histórico e convite por e-mail. #128
* CLI: hubflow user list, invite, role e grant (--revoke). #129
* CHANGELOG 0.10.0 e documentação de papéis e permissões (README e regras RN-90 a RN-97). #130

#### Polimento

* Backup .sql do banco (comando backup_db, POST/GET /api/backups para superusuários, hubflow backup). #103
* API de busca global: GET /api/search?q= em cards, projetos, clientes, usuários e etiquetas. #110
* CLI: hubflow search. #112
* Busca global na barra superior (Ctrl+K ou /), resultados agrupados com navegação por teclado; abre o card pela busca. #111

### Alterado

* Regra RN-80 atualizada: pagamento por projeto, sprint opcional (#131).

## [0.9.0] - 2026-10-14

Quadro em tempo real (SSE + Redis), presença, avatar no perfil e card com trecho da descrição.

### Adicionado

#### Quadro em tempo real

* Backend ASGI (uvicorn) com Redis no compose e eventos do projeto via pub/sub. #40
* Eventos card_created, card_moved, card_updated e card_deleted publicados a cada mudança (API, CLI e webhooks). #41
* Quadro ao vivo: endpoint SSE por projeto (token na query) e o quadro aplica os eventos sem recarregar, com indicador ao vivo/offline e reconexão automática. #42
* Presença: quem está com o quadro aberto (heartbeat com TTL no Redis, evento presence, avatares no quadro). #43

#### Polimento

* Avatar no perfil do usuário (upload, remoção, first_name e avatar_url na API). #132
* Card do quadro com trecho da descrição (2 linhas) e avatar/primeiro nome do dono. #133
* Banco de teste com nome único por checkout (suítes em paralelo).

## [0.8.0] - 2026-10-14

Sincronização com GitHub e GitLab: token por projeto, issues criadas e atualizadas a partir dos cards, importação de issues, milestones pareados com sprints e webhooks que concluem cards.

### Adicionado

#### Sincronização GitHub/GitLab

* Token e identificação do repositório por projeto (token nunca exposto), opção de criar issues e teste de conexão com GitHub/GitLab. #94
* Criar card abre a issue no GitHub/GitLab (quando o projeto pedir); número e URL da issue no card. #95
* Editar card atualiza a issue; Concluído/Arquivadas fecha e sair delas reabre. #96
* Importar issues do repositório como cards (sem duplicar, PRs de fora, fechadas em Concluído). #97
* Sprint nova pareada com o último milestone aberto do repositório (milestone segue opcional). #98
* Webhooks do GitHub (assinatura HMAC) e do GitLab (token): commit ou PR/MR mesclado com close/fixes/resolves #N conclui o card. #99
* CLI: project repo, repo-check e import-issues; card create mostra a issue aberta. #100
* Tela de integração do projeto: token, opção de criar issues, segredo e URL do webhook, teste de conexão e importação; link da issue no card. #101
* CHANGELOG 0.8.0. #102

## [0.7.0] - 2026-10-14

Dashboard: visão geral de todos os projetos, cronômetros, prazos, atividade recente, heatmap de horas e faturamento do mês.

### Adicionado

#### Dashboard

* API do dashboard: cards por coluna, em desenvolvimento agora, cronômetros abertos e totais. #88
* API do dashboard: atividade recente e prazos (vencidos e próximos 7 dias). #89
* API do dashboard: heatmap de 26 semanas (níveis 0–4) e horas da semana por projeto. #90
* API do dashboard: faturamento do mês corrente e do anterior. #91
* Tela do dashboard como página inicial: totais, cards por etapa, faturamento, em desenvolvimento, cronômetros, prazos, atividade, heatmap e horas da semana. #92
* CHANGELOG 0.7.0. #93

## [0.6.0] - 2026-10-14

Faturamento: pagamentos por sprint ou por período (mensal), resumo financeiro, CLI e tela com KPIs e gráficos.

### Adicionado

#### Faturamento por sprint

* Model Payment ligado à sprint (valor/hora, estimativas, tempo gasto, valor total, NF, datas, status, pagar e copiar). #82
* API CRUD de pagamentos com filtros (cliente, status, ano), pagar e copiar. #83
* Resumo financeiro em SQL: recebido, pendente, por cliente, por mês e anos. #84
* CLI: payment create, list, pay, copy e summary. #85
* Pagamento pertence ao projeto; sprint opcional; pagamento por período (mensal) com --month; copiar avança o mês. #131
* Tela de pagamentos: KPIs, gráficos por mês e por cliente, filtros, formulário e ações (editar, copiar, pagar, excluir). #86
* CHANGELOG 0.6.0. #87

## [0.5.0] - 2026-10-14

Controle de tempo: cronômetro por card, lançamento manual de horas, estimativa e progresso, exportação xlsx, na API, na CLI e no quadro.

### Adicionado

#### Controle de tempo

* Model TimeEntry: cronômetro por card e lançamento manual. #71
* Regra dos 15 minutos ao iniciar o cronômetro. #72
* API: iniciar/parar cronômetro, tempo do card e resumo de horas no quadro. #73
* Lançamento manual de horas; só o dono edita/apaga a própria entrada. #74
* Estimativa em horas e progresso gasto × estimado (mediana do projeto como fallback). #75
* CLI: card start abre o cronômetro; card stop, card log e card time. #76
* CLI: timesheets. #77
* Exportação xlsx do timesheet por projeto e período (entradas, por dia, por mês, por sprint). #78
* Painel do card: cronômetro, lançamento manual de horas e lista de entradas. #79
* Quadro: estimativa no painel e barra gasto × estimado no card (vermelha ao estourar), horas no card. #80
* CHANGELOG 0.5.0. #81

## [0.4.0] - 2026-10-14

Sprints numeradas por projeto, milestone opcional, projeto completo em uma chamada e polimento (menu recolhível, breadcrumb, refactor dos models).

### Adicionado

#### Sprints e milestones

* Model Sprint numerada por projeto (e Milestone opcional). #62
* Milestone opcional: regras e API. #63
* Card pertence a uma sprint (escolhida ou criada automaticamente). #64
* API de sprints. #65
* CLI: sprint create, list e close. #66
* CLI: escolha da sprint ao criar card (--sprint, pergunta, --no-input). #67
* Projeto completo em uma chamada: POST /api/projects/full e project create --full. #68
* Tela de sprints e filtro do quadro por sprint. #69
* CHANGELOG 0.4.0. #70

#### Polimento

* Menu lateral recolhível. #108
* Breadcrumb no cabeçalho. #109

### Alterado

* Refactor: abstract models (TimeStamped, Created, CreatedBy, Active) em core/models.py e managers.py por app. #117
* Exemplos de e-mail passam a usar @hubflow.com.

## [0.3.0] - 2026-10-13

Colaboração no card: comentários com @menções, etiquetas, prazo e responsável, checklist, anexos e histórico de atividade, na API, na CLI e no quadro.

### Adicionado

#### Colaboração no card

* Comentários no card. #50
* @menções em comentários e GET /api/users. #51
* Etiquetas por projeto. #52
* Prazo e responsável no card. #53
* Checklist no card. #54
* Anexos no card. #55
* Histórico de atividade do card. #56
* CLI: card comment, label, assign e due. #57
* Painel do card: comentários, @menções, etiquetas, prazo e responsável. #58
* Painel do card: checklist, anexos e atividade. #59
* Quadro: etiquetas, prazo, responsável e progresso no card; tela de etiquetas do projeto. #60
* CHANGELOG 0.3.0. #61

## [0.2.0] - 2026-10-13

Notificações por e-mail para uma ou mais pessoas, configuráveis por cliente e por projeto.

### Adicionado

#### Notificações por e-mail

* Preferências de notificação por projeto. #44
* Serviço de notificação por e-mail. #45
* Disparo nos eventos card criado, movido e concluído. #46
* CLI: project notify e project emails. #47
* Tela: notificações do projeto. #48
* CHANGELOG 0.2.0. #49

## [0.1.0] - 2026-10-13

Primeira versão utilizável: base, login por e-mail, clientes, projetos e quadro kanban, com API e CLI.

### Adicionado

#### Base e login por e-mail

* Docker Compose com Postgres 18 e Mailpit. #1
* Projeto Django 6.1.2 com uv, settings por ambiente e healthcheck. #2
* Backend no Docker Compose. #3
* Projeto Vue + Vite + Tailwind 4 no Docker Compose. #4
* Model User com login por e-mail. #5
* API: login por e-mail e senha retorna token. #6
* API: autenticação Bearer e GET /api/auth/me. #7
* API: logout invalida o token. #8
* API: esqueci minha senha envia e-mail com link. #9
* API: redefinir senha com token. #10
* API: trocar senha logado. #11
* CLI hubflow: pacote e comando login. #12
* CLI: whoami e logout. #13
* Layout base com tema claro e escuro. #14
* Tela de login. #15
* Tela esqueci minha senha. #16
* Tela redefinir senha. #17
* Guarda de rotas e menu do usuário com logout. #18

#### Clientes e projetos

* Model Cliente. #19
* API CRUD de clientes. #20
* Model Projeto com provedor GitHub/GitLab. #21
* API CRUD de projetos. #22
* CLI: client create e client list. #23
* CLI: project create e project list. #24
* Tela de clientes. #25
* Tela de projetos. #26

#### Quadro kanban

* Model Card com colunas, número sequencial e posição. #27
* API: criar card e listar o quadro. #28
* API: mover card entre colunas com reordenação. #29
* API: iniciar card e histórico de movimentações. #30
* API: editar, excluir e arquivar card. #31
* CLI: card create e card list. #32
* CLI: card move e card start. #33
* Quadro com as seis colunas. #34
* Arrastar e soltar cards. #35
* Criar e editar card no quadro. #36
* README completo. #37
* CHANGELOG 0.1.0. #38

[Unreleased]: https://github.com/rg3915/HubFlow/compare/v0.12.0...HEAD
[0.12.0]: https://github.com/rg3915/HubFlow/compare/v0.11.0...v0.12.0
[0.11.0]: https://github.com/rg3915/HubFlow/compare/v0.10.0...v0.11.0
[0.10.0]: https://github.com/rg3915/HubFlow/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/rg3915/HubFlow/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/rg3915/HubFlow/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/rg3915/HubFlow/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/rg3915/HubFlow/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/rg3915/HubFlow/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/rg3915/HubFlow/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/rg3915/HubFlow/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/rg3915/HubFlow/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/rg3915/HubFlow/releases/tag/v0.1.0
