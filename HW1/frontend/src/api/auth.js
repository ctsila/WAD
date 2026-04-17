function getDefaultApiBaseUrl() {
  return '/api'
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || getDefaultApiBaseUrl()

async function request(path, options = {}) {
  let res
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
      ...options,
    })
  } catch {
    throw new Error(`Cannot reach API at ${API_BASE_URL}. Check backend URL or CORS settings.`)
  }
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || 'Request failed')
  }
  if (res.status === 204) return null
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

export const getMe = (accessToken) =>
  request('/auth/me', {
    method: 'GET',
    headers: { Authorization: `Bearer ${accessToken}` },
  })

export const githubLogin = () => {
  window.location.href = `${API_BASE_URL}/auth/github`
}
