# HubFlow — Design

Quem usa: uma pessoa ou equipe pequena que desenvolve software para vários clientes e precisa ver, em segundos, onde cada trabalho está. O produto é uma ferramenta de uso diário, densa, lida muitas vezes por dia; a referência de densidade é Linear/GitLab, não uma página de marketing.

## Princípios

1. **A hierarquia do domínio é a navegação.** A barra lateral lista Cliente → Projetos. Nada de menu genérico "Dashboard / Projetos / Configurações" no topo.
2. **Cor só onde carrega informação.** A interface é neutra; a cor aparece nas colunas do quadro, em estados (erro, atenção) e no foco. Nada de neon, nada de gradiente.
3. **Borda encode contenção, não decoração.** Painéis têm borda fina; cards dentro de colunas usam só fundo e sombra mínima. Nunca card dentro de card.
4. **Texto em caixa normal, verbos diretos.** "Salvar alterações", "Mover para QA". Sem rótulos em caixa alta.
5. **Movimento só em resposta a ação** (abrir, mover, confirmar). Sem animações de entrada.

## Paleta

| Token | Claro | Escuro | Uso |
|---|---|---|---|
| `--bg` | `#F2F4F7` | `#14181E` | fundo da página |
| `--surface` | `#FFFFFF` | `#1C2229` | painéis, barra lateral, cards |
| `--surface-2` | `#E9ECF0` | `#242C35` | colunas do quadro, campos |
| `--border` | `#D5DAE1` | `#2F3842` | bordas |
| `--text` | `#1B2430` | `#E4E8ED` | texto |
| `--muted` | `#5D6B7A` | `#93A0AE` | texto secundário |
| `--accent` | `#245E7D` | `#6FB1D1` | ações primárias, foco, links |
| `--danger` | `#A33A2E` | `#E08A7F` | erros, excluir |

Colunas do quadro (fundo suave + ponto de cor no cabeçalho): Backlog cinza, Sprint azul-acinzentado, Em desenvolvimento âmbar `#8A6A1E`, QA roxo-acinzentado `#6B5B95`, Concluído verde `#2E6B4F`, Arquivadas cinza mais escuro.

## Tipografia

Uma família só: **IBM Plex Sans** (Google Fonts), com números tabulares nas listas. Escala: 13px (metadados), 14px (corpo da interface, line-height 1.5), 16px (formulários de autenticação), 20px (título da página, peso 600), 28px (títulos das telas de entrada, peso 600). Sem versaletes, sem itálico decorativo.

## Estrutura

```
┌──────────────┬───────────────────────────────────────────────┐
│ HubFlow      │ Título da página                 ☾  ana@…  ▾  │
│              ├───────────────────────────────────────────────┤
│ ACME         │                                               │
│   Loja       │   conteúdo                                    │
│   App        │                                               │
│ Minicom      │                                               │
│   Registri   │                                               │
│              │                                               │
│ + Cliente    │                                               │
└──────────────┴───────────────────────────────────────────────┘
```

- Barra lateral 240px, fixa; no celular vira gaveta.
- Cabeçalho de 48px com título, alternador de tema e menu do usuário.
- Conteúdo alinhado à esquerda, largura máxima 1200px nas telas de lista; o quadro ocupa toda a largura e rola na horizontal.
- Telas de autenticação: um painel centrado de 400px sobre `--bg`, com a marca em texto no topo.

Raio: 6px em botões e campos, 10px em painéis. Sombra só nos cards do quadro (`0 1px 2px rgb(0 0 0 / .06)`).

## Revisão contra os padrões genéricos

- Evitado creme + serifa + terracota; evitado preto com acento ácido. Base fria e neutra com um azul-petróleo escuro como único acento.
- Nenhum rótulo em caixa alta, nenhum "→" em botões, nenhum separador com ponto médio.
- Sem kit de cards iguais: listas são tabelas; só o quadro tem cards, e por ser o objeto do domínio.
