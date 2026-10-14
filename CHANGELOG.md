# Changelog

Todas as mudanças relevantes deste projeto são registradas aqui.

O formato segue o [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o projeto usa [versionamento semântico](https://semver.org/lang/pt-BR/).

## [0.1.0] - Em andamento

### Adicionado

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
* Model Cliente. #19
* API CRUD de clientes. #20
* Model Projeto com provedor GitHub/GitLab. #21
* API CRUD de projetos. #22
* CLI: client create e client list. #23
* CLI: project create e project list. #24
* Tela de clientes. #25
* Tela de projetos. #26
* Model Card com colunas, número sequencial e posição. #27
* API: criar card e listar o quadro. #28
* API: mover card entre colunas com reordenação. #29
* API: iniciar card e histórico de movimentações. #30
* API: editar, excluir e arquivar card. #31
* CLI: card create e card list. #32
