// Grava as respostas reais da API (só GET) para a demo sem backend (src/demo/dados/<pessoa>.json).
// Uso, com a API no ar (docker compose up):  node scripts/gravar-demo.mjs
// Cada arquivo é { "GET /caminho?query": { status, data } }, gravado com o token de cada pessoa de exemplo,
// para a demo mostrar o que cada papel enxerga (admin, desenvolvedor, leitura).
import { mkdirSync, writeFileSync } from 'node:fs'

const API = (process.env.VITE_API_URL || 'http://localhost:8000') + '/api'
const OUT = new URL('../src/demo/dados/', import.meta.url).pathname
const PESSOAS = { regis: 'regis@hubflow.com', bob: 'bob@hubflow.com', lia: 'leitura@hubflow.com' }
const SENHA = process.env.DEMO_PASSWORD || 'hubflow123'

async function login(email) {
  const r = await fetch(`${API}/auth/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, password: SENHA }) })
  if (!r.ok) throw new Error(`login de ${email} falhou: ${r.status}`)
  return (await r.json()).token
}

async function gravar(email) {
  const token = await login(email)
  const dados = {}
  const get = async (path) => {
    if (`GET ${path}` in dados) return dados[`GET ${path}`].data
    const r = await fetch(`${API}${path}`, { headers: { Authorization: `Bearer ${token}`, Accept: 'application/json' } })
    const data = r.status === 204 ? null : await r.json().catch(() => null)
    dados[`GET ${path}`] = { status: r.status, data }
    return r.ok ? data : null
  }
  const lista = (x) => (Array.isArray(x) ? x : [])

  for (const p of ['/auth/me', '/auth/social/providers', '/auth/social', '/notifications', '/me/cards', '/users', '/users/manage',
    '/users/catalog', '/report-schedules', '/payments', '/payments/summary', '/dashboard', '/dashboard/deadlines',
    '/dashboard/activity?limit=12', '/dashboard/heatmap', '/dashboard/week', '/dashboard/billing']) await get(p)

  const hoje = new Date().toISOString().slice(0, 10)  // a demo ignora a data ao procurar o relatório
  for (const c of lista(await get('/clients'))) {
    await get(`/clients/${c.id}`)
    for (const period of ['week', 'fortnight', 'month']) await get(`/reports?client=${c.id}&period=${period}&date=${hoje}`)
  }
  for (const u of lista(dados['GET /users/manage'].data)) await get(`/users/changes?user=${u.id}`)

  for (const proj of lista(await get('/projects'))) {
    const id = proj.id
    for (const s of ['', '/labels', '/sprints', '/fields', '/sla', '/form', '/automations', '/repo']) await get(`/projects/${id}${s}`)
    const quadro = await get(`/projects/${id}/board`)
    for (const coluna of quadro?.columns || []) {
      for (const card of coluna.cards || []) {
        for (const s of ['', '/comments', '/checklist', '/attachments', '/activity', '/time']) await get(`/cards/${card.id}${s}`)
      }
    }
  }
  return dados
}

mkdirSync(OUT, { recursive: true })
for (const [nome, email] of Object.entries(PESSOAS)) {
  const dados = await gravar(email)
  writeFileSync(`${OUT}${nome}.json`, JSON.stringify(dados))
  const erros = Object.values(dados).filter((r) => r.status >= 400).length
  console.log(`${nome}: ${Object.keys(dados).length} respostas (${erros} com erro, como a API devolveria)`)
}
