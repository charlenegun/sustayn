const BASE = import.meta.env.DEV ? '/api' : ''

export async function fetchTasks() {
  const r = await fetch(`${BASE}/tasks`)
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
  return r.json()
}

export async function fetchEmployees() {
  const r = await fetch(`${BASE}/employees`)
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
  return r.json()
}

export async function fetchRecommendations(taskId) {
  const r = await fetch(`${BASE}/recommendations/${taskId}`)
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
  return r.json()
}

export async function fetchTeamOverview() {
  const r = await fetch(`${BASE}/team-overview`)
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
  return r.json()
}
