const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

async function request(path, accessToken, options = {}) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  })
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

export const getMessages = (accessToken, chatId) =>
  request(`/chats/${chatId}/messages`, accessToken)

export const askQuestion = (accessToken, chatId, question) =>
  request(`/chats/${chatId}/messages/ask`, accessToken, {
    method: 'POST',
    body: JSON.stringify({ question, stream: false }),
  })

export async function askQuestionStream(accessToken, chatId, question, onToken) {
  const res = await fetch(`${API_BASE_URL}/chats/${chatId}/messages/ask`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${accessToken}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, stream: true }),
  })
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
