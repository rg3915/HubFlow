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

- **RN-80** Pagamento pertence a um projeto; a sprint é opcional. Tempo gasto = entradas da sprint ou, sem sprint, as do projeto dentro do período (mês).
- **RN-81** Status `pendente` por padrão; "pagar" marca `pago` com a data de hoje; "copiar" duplica como pendente.

## Permissões (entregável 17)

- **RN-90** Usam-se as permissões padrão do Django (`view/add/change/delete`); só existem duas específicas: `permissions.use_cli` e `permissions.view_own_payments`. Superusuário tem todas.
- **RN-91** Papéis padrão (grupos): Administrador, Gerente, Desenvolvedor, Financeiro, Cliente e Leitura. Permissões por pessoa somam às do papel.
- **RN-92** Sem `clients.view_client`, a pessoa só vê os clientes de que é membro e os projetos, cards, sprints e etiquetas deles; o resto responde 404.
- **RN-93** Sem `boards.change_card`/`delete_card`, a pessoa só edita, move, exclui e arquiva os próprios cards (criado por ela ou com ela de responsável). Anexos seguem a regra do card; apagar comentário de outro exige `boards.delete_comment`.
- **RN-94** Pagamentos: `billing.view_payment` vê todos, `view_own_payments` só os dos seus clientes, sem nenhuma das duas não vê; criar, editar/pagar/copiar e excluir exigem `add/change/delete_payment`.
- **RN-95** O login pela CLI (`X-HubFlow-Client: cli`) exige `use_cli`; o token da CLI deixa de valer se a permissão for retirada.
- **RN-96** O convite cria a pessoa sem senha e manda o link para defini-la (mesmo fluxo da redefinição, RN-04).
- **RN-97** Toda mudança de papel, permissão por pessoa, vínculo, situação ou convite fica registrada com quem fez, quando, o antes e o depois.

## Campos personalizados e formulários (entregável 7)

- **RN-100** Cada projeto define seus campos (texto, número, data, seleção, sim/não), com nome único no projeto e ordem. O valor é validado pelo tipo; na seleção, só as opções do campo. Obrigatórios são exigidos ao criar o card e não podem ser esvaziados depois; ao editar, só os campos enviados são checados. Mudanças de valores entram no histórico.
- **RN-101** O formulário público do projeto, quando ligado, cria card no Backlog sem login a partir de um link com token. Gerar outro link invalida o anterior. Os envios têm limite por IP e hora (`FORM_SUBMISSIONS_PER_HOUR`).

## Automações e SLA (entregável 8)

- **RN-110** Automação do projeto = gatilho (card criado, card entrou na coluna X, SLA estourado em uma coluna ou em qualquer) → ação (mover para coluna, definir responsável, adicionar etiqueta do projeto, avisar quem criou e o responsável). Só as ligadas rodam; uma ação de automação não dispara outra automação. Cada execução entra no histórico do card.
- **RN-111** SLA por coluna = horas máximas que o card pode ficar nela, contadas a partir de quando entrou na coluna. O estouro é verificado a cada 15 minutos (`check_sla`), dispara as automações de SLA uma vez por card e coluna e volta a contar se o card sair e voltar.
- **RN-112** Card com prazo vencido, fora de Concluído e Arquivadas, avisa o responsável no sino uma vez por prazo (de novo se o prazo mudar).

## Versionamento

- **RN-50** O CHANGELOG segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e versionamento semântico. Começa em 0.1.0 e cada entregável concluído gera uma versão.
