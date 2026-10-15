export const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Arquivos (anexos, avatares): caminho relativo no disco local da API ou URL completa no S3.
export const mediaUrl = (url) => (!url ? null : /^https?:\/\//.test(url) ? url : BASE_URL + url)

export class ApiError extends Error {
  constructor(status, detail) {
    super(detail)
    this.status = status
  }
}

export async function api(path, { method = 'GET', body, token, form } = {}) {
  // Demo sem backend (GitHub Pages): o módulo só entra no build com VITE_DEMO=1.
  if (import.meta.env.VITE_DEMO === '1') return (await import('./demo/api.js')).demoApi(path, { method, body, token })
  const headers = { Accept: 'application/json' }
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (token) headers.Authorization = `Bearer ${token}`

  let response
  try {
    // `form` é um FormData (upload); o navegador define o Content-Type com o boundary.
    const payload = form || (body && JSON.stringify(body))
    response = await fetch(`${BASE_URL}/api${path}`, { method, headers, body: payload })
  } catch {
    throw new ApiError(0, 'Não foi possível falar com o servidor. Verifique sua conexão.')
  }

  if (response.status === 204) return null
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new ApiError(response.status, data.detail || 'Algo deu errado. Tente de novo.')
  return data
}
