# HubFlow — Regras de negócio

Numeradas para serem citadas em issues, testes e commits (ex.: `RN-07`).

## Usuários e acesso

- **RN-01** O e-mail identifica o usuário e é único (comparação sem diferenciar maiúsculas).
- **RN-02** Senha com no mínimo 8 caracteres, validada pelos validadores padrão do Django.
- **RN-03** O pedido de redefinição de senha responde sempre com sucesso, exista ou não o e-mail, para não revelar quem está cadastrado.
- **RN-04** O token de redefinição é de uso único e expira em 24 horas.
- **RN-05** Um usuário pode ter vários tokens de API (um por dispositivo/CLI). Logout invalida só o token usado.
- **RN-06** Toda rota da API, exceto login e redefinição de senha, exige token válido.

## Clientes

- **RN-10** Nome do cliente é obrigatório e único.
- **RN-11** Cliente só pode ser excluído se não tiver projetos; caso contrário, deve ser arquivado (`is_active = false`).
- **RN-12** A lista de e-mails do cliente é opcional e aceita um ou mais endereços.

## Projetos

- **RN-20** Projeto pertence a exatamente um cliente.
- **RN-21** Nome do projeto é único dentro do cliente.
- **RN-22** Provedor é `github` ou `gitlab`. `owner` e `repo` são obrigatórios; o par `(provider, owner, repo)` é único no sistema (um repositório = um projeto).
- **RN-23** A lista de e-mails do projeto é opcional. Quando vazia, a notificação usa a lista do cliente.
- **RN-24** Excluir um projeto arquiva seus cards em vez de apagá-los.

## Quadro e cards

- **RN-30** As colunas são fixas e nesta ordem: Backlog → Sprint → Em desenvolvimento → QA → Concluído → Arquivadas.
- **RN-31** Card novo entra no Backlog, na última posição.
- **RN-32** Cada card tem um número sequencial por projeto, começando em 1, nunca reaproveitado.
- **RN-33** Dentro de uma coluna, as posições são inteiros consecutivos a partir de 0. Mover um card reordena a coluna de origem e a de destino.
- **RN-34** `position` omitido ao mover = última posição da coluna de destino.
- **RN-35** Qualquer card pode ir para qualquer coluna (não há transição proibida). O histórico de movimentações é registrado com data, usuário, coluna de origem e destino.
- **RN-36** "Iniciar" um card é movê-lo para Em desenvolvimento.
- **RN-37** Cards arquivados não aparecem no quadro por padrão; aparecem com `?archived=true`.
- **RN-38** Título do card é obrigatório (até 200 caracteres).

## Notificações por e-mail (entregável 4)

- **RN-40** Destinatários = e-mails do projeto; se vazio, e-mails do cliente; se vazio, ninguém.
- **RN-41** Eventos que notificam: card criado, card movido, card concluído. Cada um pode ser ligado/desligado por projeto.
- **RN-42** O e-mail traz o nome do cliente, do projeto, o número e título do card e o link para ele.

## Comentários, etiquetas e anexos (entregável 5)

- **RN-43** Só o autor edita ou exclui o próprio comentário; só quem enviou exclui o próprio anexo.
- **RN-44** `@email` ou `@nome` de usuário ativo no comentário vira menção e avisa o mencionado por e-mail; o autor não é avisado de si mesmo.
- **RN-45** Nome de etiqueta é único por projeto (sem diferenciar maiúsculas); um card só recebe etiquetas do próprio projeto.
- **RN-46** Card vencido = prazo no passado e coluna diferente de Concluído e Arquivadas.
- **RN-47** Anexo tem tamanho máximo configurável (padrão 10 MB).

## Sprints e milestones (entregável 13)

- **RN-60** Sprint tem número sequencial por projeto; milestone é opcional.
- **RN-61** Todo card pertence a uma sprint. Sprint informada → usa; não informada → última sprint aberta; nenhuma → cria a sprint 1. Na CLI, sem `--sprint`, pergunta se quer criar uma nova.
- **RN-62** Fechar uma sprint não move cards; eles seguem no quadro.

## Controle de tempo (entregável 9)

- **RN-70** Um cronômetro aberto por card. Cronômetros abertos em cards diferentes são permitidos, sem confirmação.
- **RN-71** Iniciar um cronômetro no mesmo projeto menos de 15 minutos depois do último parar faz o novo começar onde o anterior terminou.
- **RN-72** Horas podem ser lançadas manualmente por card (quantidade, data, nota).
- **RN-73** Só o dono de uma entrada de tempo (cronômetro ou manual) pode excluí-la.
- **RN-74** `card start` move para Em desenvolvimento e abre o cronômetro; `card stop` só fecha o cronômetro.
- **RN-75** Sem estimativa no card, o progresso usa a mediana das últimas tarefas concluídas do projeto.

## Faturamento (entregável 14)

- **RN-80** Pagamento pertence a uma sprint. Tempo gasto = soma das entradas de tempo dos cards da sprint.
- **RN-81** Status `pendente` por padrão; "pagar" marca `pago` com a data de hoje; "copiar" duplica como pendente.

## Versionamento

- **RN-50** O CHANGELOG segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e versionamento semântico. Começa em 0.1.0 e cada entregável concluído gera uma versão.
