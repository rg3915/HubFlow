// API simulada da demo (build com VITE_DEMO=1, sem backend).
// Leituras: respostas reais gravadas por scripts/gravar-demo.mjs, uma por pessoa de exemplo (o token diz quem é).
// Escritas: mover/criar card, comentar e lançar tempo mudam o estado em memória, salvo no localStorage do visitante.
// O resto responde que não está disponível na demo.
import { ApiError } from '../api'
import bob from './dados/bob.json'
import lia from './dados/lia.json'
import regis from './dados/regis.json'

const GRAVADOS = { regis, bob, lia }
export const PESSOAS = {
  regis: { email: 'regis@hubflow.com', name: 'Regis Santos', papel: 'administrador' },
  bob: { email: 'bob@hubflow.com', name: 'Bob Silva', papel: 'desenvolvedor no ACME' },
  lia: { email: 'leitura@hubflow.com', name: 'Lia Leitura', papel: 'só leitura no ACME' },
}
const INDISPONIVEL = 'Indisponível na demo: aqui nada vai para um servidor. Rode o HubFlow na sua máquina para usar tudo.'
const IGNORADOS = ['date', 'start', 'end']  // o relatório gravado vale para qualquer dia

const estados = {}
function estado(pessoa) {
  if (!estados[pessoa]) {
    let salvo = null
    try { salvo = JSON.parse(localStorage.getItem(`demo:${pessoa}`)) } catch { /* sem localStorage: começa do gravado */ }
    estados[pessoa] = salvo || structuredClone(GRAVADOS[pessoa])
  }
  return estados[pessoa]
}
function salvar(pessoa) {
  try { localStorage.setItem(`demo:${pessoa}`, JSON.stringify(estados[pessoa])) } catch { /* cheio ou bloqueado: segue só em memória */ }
}
export function restaurarDemo() {
  for (const pessoa of Object.keys(GRAVADOS)) {
    delete estados[pessoa]
    try { localStorage.removeItem(`demo:${pessoa}`) } catch { /* nada a limpar */ }
  }
}

// GET: igual ao gravado; senão o mesmo caminho com os mesmos filtros (sem data); senão qualquer resposta boa do caminho.
function ler(dados, path) {
  const exata = dados[`GET ${path}`]
  if (exata) return exata
  const [rota, query = ''] = path.split('?')
  const filtros = (q) => [...new URLSearchParams(q)].filter(([k]) => !IGNORADOS.includes(k)).sort().join('&')
  const candidatas = Object.entries(dados).filter(([k]) => k.split('?')[0] === `GET ${rota}`)
  const mesmaConsulta = candidatas.find(([k]) => filtros(k.split('?')[1] || '') === filtros(query))
  return (mesmaConsulta || candidatas.find(([, r]) => r.status < 400))?.[1]
}

const agora = () => new Date().toISOString()
const proximoId = (lista) => Math.max(0, ...lista.map((x) => x.id || 0)) + 1
const quadros = (dados) => Object.entries(dados).filter(([k, r]) => /^GET \/projects\/\d+\/board$/.test(k) && r.status === 200).map(([, r]) => r.data)
function acharCard(dados, id) {
  for (const quadro of quadros(dados)) {
    for (const coluna of quadro.columns) {
      const card = coluna.cards.find((c) => c.id === id)
      if (card) return { quadro, coluna, card }
    }
  }
  return null
}
const eu = (dados) => {
  const { id, uuid, email, name, first_name, avatar_url } = dados['GET /auth/me'].data
  return { id, uuid, email, name, first_name, avatar_url }
}
function tempo(dados, cardId) {
  const chave = `GET /cards/${cardId}/time`
  dados[chave] ||= { status: 200, data: { entries: [], total_hours: 0, running: null } }
  return dados[chave].data
}
const horas = (inicio, fim) => Math.round(((new Date(fim) - new Date(inicio)) / 3600000) * 100) / 100

// Escritas simuladas: [método, padrão, (dados, partes, corpo) => resposta]
const ACOES = [
  ['POST', /^\/cards\/(\d+)\/move$/, (dados, [id], { column, position = 0 }) => {
    const achado = acharCard(dados, +id)
    if (!achado) throw new ApiError(404, 'Card não encontrado.')
    const { quadro, coluna, card } = achado
    coluna.cards.splice(coluna.cards.indexOf(card), 1)
    card.column = column
    quadro.columns.find((c) => c.key === column)?.cards.splice(position, 0, card)
    return card
  }],
  ['POST', /^\/projects\/(\d+)\/cards$/, (dados, [projectId], { title, description = '', fields = {} }) => {
    const quadro = dados[`GET /projects/${projectId}/board`]?.data
    if (!quadro) throw new ApiError(404, 'Projeto não encontrado.')
    const todos = quadro.columns.flatMap((c) => c.cards)
    const card = {
      ...structuredClone(todos[0] || {}), id: proximoId(todos), number: Math.max(0, ...todos.map((c) => c.number)) + 1,
      title, description, column: 'backlog', custom_values: fields, labels: [], assignee: null, created_by: eu(dados),
      is_overdue: false, checklist: { done: 0, total: 0 }, attachments_count: 0, time: { hours: 0, running: false },
      progress: { spent_hours: 0, estimate_hours: null, percent: null, source: null }, sla: null, issue_number: null, issue_url: null,
    }
    quadro.columns.find((c) => c.key === 'backlog').cards.push(card)
    return card
  }],
  ['POST', /^\/cards\/(\d+)\/comments$/, (dados, [id], { text }) => {
    const chave = `GET /cards/${id}/comments`
    dados[chave] ||= { status: 200, data: [] }
    const comentario = { card_id: +id, author: eu(dados), mentions: [], id: proximoId(dados[chave].data), text, created: agora() }
    dados[chave].data.push(comentario)
    return comentario
  }],
  ['POST', /^\/cards\/(\d+)\/timer\/start$/, (dados, [id]) => {
    const t = tempo(dados, id)
    t.running = { card_id: +id, user: eu(dados), is_running: true, hours: 0, id: proximoId(t.entries), started_at: agora(), ended_at: null, note: '', is_manual: false }
    return t.running
  }],
  ['POST', /^\/cards\/(\d+)\/timer\/stop$/, (dados, [id]) => {
    const t = tempo(dados, id)
    if (!t.running) throw new ApiError(400, 'Nenhum cronômetro rodando neste card.')
    const fim = agora()
    const entrada = { ...t.running, is_running: false, ended_at: fim, hours: horas(t.running.started_at, fim) }
    t.entries.unshift(entrada)
    t.total_hours = Math.round((t.total_hours + entrada.hours) * 100) / 100
    t.running = null
    return entrada
  }],
  ['POST', /^\/cards\/(\d+)\/time-entries$/, (dados, [id], { hours, date, note = '' }) => {
    const t = tempo(dados, id)
    const entrada = { card_id: +id, user: eu(dados), is_running: false, hours: +hours, id: proximoId(t.entries), started_at: `${date}T09:00:00`, ended_at: null, note, is_manual: true }
    t.entries.unshift(entrada)
    t.total_hours = Math.round((t.total_hours + entrada.hours) * 100) / 100
    return entrada
  }],
]

export async function demoApi(path, { method = 'GET', body = {}, token } = {}) {
  if (path === '/auth/login') {
    const pessoa = Object.keys(PESSOAS).find((p) => PESSOAS[p].email === body.email?.trim().toLowerCase())
    if (!pessoa) throw new ApiError(401, 'Na demo, entre como regis@hubflow.com, bob@hubflow.com ou leitura@hubflow.com (qualquer senha).')
    return { token: `demo-${pessoa}` }
  }
  if (path === '/auth/logout') return null
  if (path === '/auth/social/providers') return []
  const pessoa = token?.startsWith('demo-') && token.slice(5)
  if (!GRAVADOS[pessoa]) throw new ApiError(401, 'Sessão inválida.')
  const dados = estado(pessoa)

  if (method === 'GET') {
    const r = ler(dados, path)
    if (!r) throw new ApiError(404, INDISPONIVEL)
    if (r.status >= 400) throw new ApiError(r.status, r.data?.detail || 'Você não tem permissão para isto.')
    return structuredClone(r.data)
  }
  // quem só lê (papel Leitura) não escreve nada, como na API de verdade
  const me = dados['GET /auth/me'].data
  if (!me.is_superuser && me.roles.length && me.roles.every((r) => r === 'Leitura')) throw new ApiError(403, 'Você não tem permissão para isto.')
  for (const [m, padrao, fazer] of ACOES) {
    const partes = method === m && path.match(padrao)
    if (partes) {
      const resposta = fazer(dados, partes.slice(1), body || {})
      salvar(pessoa)
      return structuredClone(resposta)
    }
  }
  throw new ApiError(400, INDISPONIVEL)
}
