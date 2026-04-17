function getDefaultApiBaseUrl() {
  if (typeof window === 'undefined') return 'http://localhost:8000'
  const { protocol, hostname } = window.location

  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return `${protocol}//${hostname}:8000`
  }

  // Support hosts like "...-5173.app.github.dev" by swapping forwarded port in hostname.
  if (/-(\d+)\./.test(hostname)) {
    return `${protocol}//${hostname.replace(/-\d+\./, '-8000.')}`
  }

  return `${protocol}//${hostname}:8000`
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || getDefaultApiBaseUrl()

async function request(path, accessToken, options = {}) {
  let res
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
        ...(options.headers || {}),
      },
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

export const createChat = (accessToken, title = 'New Chat') =>
  request('/chats', accessToken, { method: 'POST', body: JSON.stringify({ title }) })

export const getChats = (accessToken) => request('/chats', accessToken)

export const deleteChat = (accessToken, chatId) =>
  request(`/chats/${chatId}`, accessToken, { method: 'DELETE' })

export const renameChat = (accessToken, chatId, title) =>
  request(`/chats/${chatId}`, accessToken, {
    method: 'PATCH',
    body: JSON.stringify({ title }),
  })

export const getMessages = (accessToken, chatId) =>
  request(`/chats/${chatId}/messages`, accessToken)

export const askQuestion = (accessToken, chatId, question) =>
  request(`/chats/${chatId}/messages/ask`, accessToken, {
    method: 'POST',
    body: JSON.stringify({ question, stream: false }),
  })

export async function askQuestionStream(accessToken, chatId, question, onToken) {
  let res
  try {
    res = await fetch(`${API_BASE_URL}/chats/${chatId}/messages/ask`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${accessToken}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, stream: true }),
    })
  } catch {
    throw new Error(`Cannot reach API at ${API_BASE_URL}. Check backend URL or CORS settings.`)
  }
  if (!res.ok || !res.body) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || 'Streaming failed')
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let done = false
  while (!done) {
    const chunk = await reader.read()
    done = chunk.done
    if (chunk.value) {
      const text = decoder.decode(chunk.value, { stream: true })
      text
        .split('\n\n')
        .map((line) => line.replace(/^data:\s*/, ''))
        .filter(Boolean)
        .forEach((token) => onToken(token))
    }
  }
}
