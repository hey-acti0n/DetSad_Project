const API_BASE = '/api/v1'

function getCsrfToken() {
  const m = document.cookie.match(/csrftoken=([^;]+)/)
  return m ? m[1].trim() : null
}

const fetchOpts = (method, body, credentials = 'include') => {
  const headers = {}
  if (body) headers['Content-Type'] = 'application/json'
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    const csrf = getCsrfToken()
    if (csrf) headers['X-CSRFToken'] = csrf
  }
  return { method, headers, body: body ? JSON.stringify(body) : undefined, credentials }
}

export async function getGroups() {
  const r = await fetch(`${API_BASE}/groups`, fetchOpts('GET'))
  if (!r.ok) throw new Error('Не удалось загрузить список групп')
  return r.json()
}

export async function getChildren() {
  const r = await fetch(`${API_BASE}/children`, fetchOpts('GET'))
  if (!r.ok) throw new Error('Не удалось загрузить список детей')
  return r.json()
}

export async function getGameActions() {
  const r = await fetch(`${API_BASE}/game/actions`, fetchOpts('GET'))
  if (!r.ok) throw new Error('Не удалось загрузить правила')
  return r.json()
}

export async function gameInteraction(childId, actionId) {
  const r = await fetch(`${API_BASE}/game/interaction`, fetchOpts('POST', { childId, actionId }))
  const data = await r.json()
  return data
}

export async function adminLogin(username, password) {
  const r = await fetch(`${API_BASE}/admin/login`, fetchOpts('POST', { username, password }))
  const data = await r.json()
  if (!r.ok) throw new Error(data.error || 'Ошибка входа')
  return data
}

export async function adminLogout() {
  await fetch(`${API_BASE}/admin/logout`, fetchOpts('POST', null))
}

export async function adminStatsGroups(from, to) {
  const params = new URLSearchParams()
  if (from) params.set('from', from)
  if (to) params.set('to', to)
  const r = await fetch(`${API_BASE}/admin/stats/groups?${params}`, fetchOpts('GET'))
  if (!r.ok) throw new Error('Ошибка загрузки')
  return r.json()
}

export async function adminStatsChildren(groupId, q, from, to) {
  const params = new URLSearchParams()
  if (groupId) params.set('groupId', groupId)
  if (q) params.set('q', q)
  if (from) params.set('from', from)
  if (to) params.set('to', to)
  const r = await fetch(`${API_BASE}/admin/stats/children?${params}`, fetchOpts('GET'))
  if (!r.ok) throw new Error('Ошибка загрузки')
  return r.json()
}

export async function adminChildEvents(childId, from, to) {
  const params = new URLSearchParams()
  if (from) params.set('from', from)
  if (to) params.set('to', to)
  const r = await fetch(`${API_BASE}/admin/child/${childId}/events?${params}`, fetchOpts('GET'))
  if (!r.ok) throw new Error('Ошибка загрузки')
  return r.json()
}

export async function adminMonthlyResults(groupId) {
  const params = new URLSearchParams()
  if (groupId) params.set('group_id', groupId)
  const r = await fetch(`${API_BASE}/admin/monthly-results?${params}`, fetchOpts('GET'))
  if (!r.ok) throw new Error('Ошибка загрузки')
  return r.json()
}

export async function adminMonthlyStats(year, month, groupId) {
  const params = new URLSearchParams({ year: String(year), month: String(month) })
  if (groupId) params.set('group_id', groupId)
  const r = await fetch(`${API_BASE}/admin/monthly-stats?${params}`, fetchOpts('GET'))
  if (!r.ok) {
    const data = await r.json().catch(() => ({}))
    throw new Error(data.error || 'Ошибка загрузки')
  }
  return r.json()
}

export async function adminEvents(groupId, childId, from, to) {
  const params = new URLSearchParams()
  if (groupId) params.set('groupId', groupId)
  if (childId) params.set('childId', childId)
  if (from) params.set('from', from)
  if (to) params.set('to', to)
  const r = await fetch(`${API_BASE}/admin/events?${params}`, fetchOpts('GET'))
  if (!r.ok) throw new Error('Ошибка загрузки')
  return r.json()
}

export async function adminBalanceAdjust(childId, delta, comment) {
  const r = await fetch(`${API_BASE}/admin/child/${childId}/balance-adjust`, fetchOpts('POST', { delta, comment }))
  const data = await r.json()
  if (!r.ok) throw new Error(data.error || 'Ошибка')
  return data
}

export async function adminCheckAuth() {
  const r = await fetch(`${API_BASE}/admin/stats/groups`, fetchOpts('GET'))
  return r.ok
}

export async function adminMe() {
  const r = await fetch(`${API_BASE}/admin/me`, fetchOpts('GET'))
  if (!r.ok) throw new Error('Ошибка')
  return r.json()
}

export async function adminGroupsList() {
  const r = await fetch(`${API_BASE}/admin/groups`, fetchOpts('GET'))
  if (!r.ok) throw new Error('Ошибка загрузки групп')
  return r.json()
}

export async function adminGroupCreate(name) {
  const r = await fetch(`${API_BASE}/admin/group/create`, fetchOpts('POST', { name }))
  const data = await r.json()
  if (!r.ok) throw new Error(data.error || 'Ошибка')
  return data
}

export async function adminGroupUpdate(id, name) {
  const r = await fetch(`${API_BASE}/admin/group/${id}`, fetchOpts('PUT', { name }))
  const data = await r.json()
  if (!r.ok) throw new Error(data.error || 'Ошибка')
  return data
}

export async function adminGroupDelete(id) {
  const r = await fetch(`${API_BASE}/admin/group/${id}`, fetchOpts('DELETE'))
  const data = await r.json()
  if (!r.ok) throw new Error(data.error || 'Ошибка')
  return data
}

export async function adminChildCreate(fullName, groupId) {
  const r = await fetch(`${API_BASE}/admin/children/create`, fetchOpts('POST', { fullName, groupId: groupId || null }))
  const data = await r.json()
  if (!r.ok) throw new Error(data.error || 'Ошибка')
  return data
}

export async function adminChildUpdate(id, fullName, groupId) {
  const r = await fetch(`${API_BASE}/admin/child/${id}/update`, fetchOpts('PUT', { fullName, groupId: groupId || null }))
  const data = await r.json()
  if (!r.ok) throw new Error(data.error || 'Ошибка')
  return data
}

export async function adminChildDelete(id) {
  const r = await fetch(`${API_BASE}/admin/child/${id}/delete`, fetchOpts('DELETE'))
  const data = await r.json()
  if (!r.ok) throw new Error(data.error || 'Ошибка')
  return data
}
