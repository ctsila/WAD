import { useEffect, useMemo, useState } from 'react'
import { BrowserRouter, Navigate, Route, Routes, useNavigate } from 'react-router-dom'
import { githubLogin, login, logout, register } from './api/auth'
import { askQuestion, askQuestionStream, createChat, deleteChat, getChats, getMessages } from './api/chats'
import { AuthProvider, useAuth } from './utils/auth.jsx'
import './index.css'

function AuthPage() {
  const [tab, setTab] = useState('signin')
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const { setTokens, isAuthenticated } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (isAuthenticated) navigate('/')
  }, [isAuthenticated, navigate])

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    try {
      const data =
        tab === 'signin'
          ? await login({ username, password })
          : await register({ username, email, password })
      setTokens(data.access_token, data.refresh_token)
      navigate('/')
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="auth-page">
      <div className="card">
        <div className="tabs">
          <button className={tab === 'signin' ? 'active' : ''} onClick={() => setTab('signin')}>Sign in</button>
          <button className={tab === 'register' ? 'active' : ''} onClick={() => setTab('register')}>Register</button>
        </div>
        <form onSubmit={onSubmit} className="form">
          <input placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} required />
          {tab === 'register' && (
            <input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          )}
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button type="submit">{tab === 'signin' ? 'Sign in' : 'Register'}</button>
          <button type="button" className="secondary" onClick={githubLogin}>Continue with GitHub</button>
          {error && <p className="error">{error}</p>}
        </form>
      </div>
    </div>
  )
}

function ChatPage() {
  const { accessToken, refreshToken, clearTokens } = useAuth()
  const [chats, setChats] = useState([])
  const [activeChatId, setActiveChatId] = useState(null)
  const [messages, setMessages] = useState([])
  const [question, setQuestion] = useState('')
  const [stream, setStream] = useState(false)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const activeChat = useMemo(() => chats.find((c) => c.id === activeChatId), [chats, activeChatId])

  useEffect(() => {
    if (!accessToken) return
    getChats(accessToken).then((data) => {
      setChats(data)
      if (data[0]) setActiveChatId(data[0].id)
    })
  }, [accessToken])

  useEffect(() => {
    if (!accessToken || !activeChatId) return
    getMessages(accessToken, activeChatId).then((data) => setMessages(data))
  }, [accessToken, activeChatId])

  async function onCreateChat() {
    const chat = await createChat(accessToken)
    setChats((prev) => [chat, ...prev])
    setActiveChatId(chat.id)
    setMessages([])
  }

  async function onDeleteChat(chatId) {
    await deleteChat(accessToken, chatId)
    const next = chats.filter((c) => c.id !== chatId)
    setChats(next)
    if (activeChatId === chatId) {
      setActiveChatId(next[0]?.id || null)
      setMessages([])
    }
  }

  async function onLogout() {
    if (refreshToken) {
      try {
        await logout(refreshToken, accessToken)
      } catch {
        console.error('logout failed')
      }
    }
    clearTokens()
    navigate('/auth')
  }

  async function onSend() {
    if (!question.trim() || !activeChatId) return
    const q = question
    setQuestion('')
    setLoading(true)
    setMessages((prev) => [...prev, { id: `tmp-u-${Date.now()}`, role: 'user', content: q }])

    try {
      if (!stream) {
        const data = await askQuestion(accessToken, activeChatId, q)
        setMessages((prev) => [...prev, { id: `tmp-a-${Date.now()}`, role: 'assistant', content: data.answer }])
      } else {
        let buffer = ''
        const assistantId = `tmp-a-${Date.now()}`
        setMessages((prev) => [...prev, { id: assistantId, role: 'assistant', content: '' }])
        await askQuestionStream(accessToken, activeChatId, q, (token) => {
          buffer += token
          setMessages((prev) => prev.map((m) => (m.id === assistantId ? { ...m, content: buffer } : m)))
        })
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <button onClick={onCreateChat}>New Chat</button>
        <button onClick={onLogout} className="secondary">Logout</button>
        <div className="chat-list">
          {chats.map((chat) => (
            <div key={chat.id} className={`chat-item ${activeChatId === chat.id ? 'active' : ''}`}>
              <button onClick={() => setActiveChatId(chat.id)}>{chat.title}</button>
              <button className="danger" onClick={() => onDeleteChat(chat.id)}>x</button>
            </div>
          ))}
        </div>
      </aside>
      <main className="main">
        <h2>{activeChat?.title || 'Select a chat'}</h2>
        <div className="messages">
          {messages.map((m) => (
            <div key={m.id} className={`message ${m.role}`}>
              <strong>{m.role}:</strong> {m.content}
            </div>
          ))}
        </div>
        <div className="input-bar">
          <textarea value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Type your question..." />
          <label>
            <input type="checkbox" checked={stream} onChange={(e) => setStream(e.target.checked)} /> Stream
          </label>
          <button onClick={onSend} disabled={loading}>{loading ? 'Loading...' : 'Send'}</button>
        </div>
      </main>
    </div>
  )
}

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth()
  if (!isAuthenticated) return <Navigate to="/auth" replace />
  return children
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/auth" element={<AuthPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <ChatPage />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  )
}
