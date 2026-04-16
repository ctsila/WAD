const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || 'Request failed')
  }
  return res.json()
}

export const register = (payload) =>
  request('/auth/register', { method: 'POST', body: JSON.stringify(payload) })

export const login = (payload) =>
  request('/auth/login', { method: 'POST', body: JSON.stringify(payload) })

export const refreshToken = (refresh_token) =>
  request('/auth/refresh', { method: 'POST', body: JSON.stringify({ refresh_token }) })

export const logout = (refresh_token, accessToken) =>
  request('/auth/logout', {
    method: 'POST',
    headers: { Authorization: `Bearer ${accessToken}` },
    body: JSON.stringify({ refresh_token }),
  })

export const githubLogin = () => {
  window.location.href = `${API_BASE_URL}/auth/github`
}
