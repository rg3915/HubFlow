# Changelog

Todas as mudanças relevantes deste projeto são registradas aqui.

O formato segue o [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o projeto usa [versionamento semântico](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Adicionado

* Comentários no card. #50
* @menções em comentários e GET /api/users. #51
* Etiquetas por projeto. #52
* Prazo e responsável no card. #53
* Checklist no card. #54
* Anexos no card. #55
* Histórico de atividade do card. #56
* CLI: card comment, label, assign e due. #57

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

[Unreleased]: https://github.com/rg3915/HubFlow/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/rg3915/HubFlow/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/rg3915/HubFlow/releases/tag/v0.1.0
