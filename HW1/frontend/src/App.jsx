import { useEffect, useMemo, useState } from 'react'
import { BrowserRouter, Navigate, Route, Routes, useNavigate } from 'react-router-dom'
import { getMe, githubLogin, login, logout, register } from './api/auth'
import { askQuestion, askQuestionStream, createChat, deleteChat, getChats, getMessages, renameChat } from './api/chats'
import { AuthProvider, useAuth } from './utils/auth.jsx'
import './index.css'

const USERNAME_RULE = /^[A-Za-z0-9._-]{3,24}$/
const EMAIL_RULE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

function isPasswordValid(password) {
  return password.length >= 8 && /[A-Za-z]/.test(password) && /\d/.test(password)
}

function ThemeToggle({ theme, onToggle }) {
  return (
    <button type="button" className="theme-toggle" onClick={onToggle}>
      {theme === 'dark' ? 'Light mode' : 'Dark mode'}
    </button>
  )
}

function FieldHint({ title, items }) {
  return (
    <div className="field-hint" role="note" aria-label={title}>
      <p>{title}</p>
      <ul>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  )
}

function AuthPage({ theme, toggleTheme }) {
  const [tab, setTab] = useState('signin')
  const [identifier, setIdentifier] = useState('')
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [hoveredField, setHoveredField] = useState(null)
  const { setTokens, isAuthenticated } = useAuth()
  const navigate = useNavigate()

  const signinReady = identifier.trim().length > 0 && password.trim().length > 0
  const usernameReady = USERNAME_RULE.test(username.trim())
  const emailReady = EMAIL_RULE.test(email.trim())
  const passwordReady = isPasswordValid(password.trim())
  const registerReady = usernameReady && emailReady && passwordReady

  useEffect(() => {
    if (isAuthenticated) navigate('/')
  }, [isAuthenticated, navigate])

  useEffect(() => {
    setError('')
  }, [tab])

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    if (tab === 'signin' && !signinReady) return
    if (tab === 'register' && !registerReady) return

    try {
      const data =
        tab === 'signin'
          ? await login({ username: identifier.trim(), password: password.trim() })
          : await register({ username: username.trim(), email: email.trim(), password: password.trim() })
      setTokens(data.access_token, data.refresh_token)
      navigate('/')
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="auth-page">
      <div className="card">
        <div className="card-head">
          <h1>Chat Studio</h1>
          <ThemeToggle theme={theme} onToggle={toggleTheme} />
        </div>
        <div className="tabs">
          <button className={tab === 'signin' ? 'active' : ''} onClick={() => setTab('signin')}>Sign in</button>
          <button className={tab === 'register' ? 'active' : ''} onClick={() => setTab('register')}>Register</button>
        </div>
        <form onSubmit={onSubmit} className="form">
          {tab === 'signin' ? (
            <div className="field-wrap">
              <input
                placeholder="Username or email"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                required
              />
            </div>
          ) : (
            <div className="field-wrap" onMouseEnter={() => setHoveredField('username')} onMouseLeave={() => setHoveredField(null)}>
              <input
                placeholder="Username"
                value={username}
                onFocus={() => setHoveredField('username')}
                onBlur={() => setHoveredField(null)}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
              {hoveredField === 'username' && (
                <FieldHint
                  title="Username rules"
                  items={['3-24 characters', 'Use letters, numbers, . _ -', 'No spaces']}
                />
              )}
            </div>
          )}
          {tab === 'register' && (
            <div className="field-wrap">
              <input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>
          )}
          <div className="field-wrap" onMouseEnter={() => setHoveredField('password')} onMouseLeave={() => setHoveredField(null)}>
            <input
              type="password"
              placeholder="Password"
              value={password}
              onFocus={() => setHoveredField('password')}
              onBlur={() => setHoveredField(null)}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            {tab === 'register' && hoveredField === 'password' && (
              <FieldHint
                title="Password rules"
                items={['At least 8 characters', 'Include at least 1 letter', 'Include at least 1 number']}
              />
            )}
          </div>
          <button type="submit" className={tab === 'signin' ? (signinReady ? 'ready' : '') : (registerReady ? 'ready' : '')} disabled={tab === 'signin' ? !signinReady : !registerReady}>
            {tab === 'signin' ? 'Sign in' : 'Register'}
          </button>
          <button type="button" className="secondary" onClick={githubLogin}>Continue with GitHub</button>
          {error && <p className="error">{error}</p>}
        </form>
      </div>
    </div>
  )
}

function ChatPage({ theme, toggleTheme }) {
  const { accessToken, refreshToken, clearTokens } = useAuth()
  const [chats, setChats] = useState([])
  const [activeChatId, setActiveChatId] = useState(null)
  const [messages, setMessages] = useState([])
  const [question, setQuestion] = useState('')
  const [me, setMe] = useState(null)
  const [stream, setStream] = useState(false)
  const [loading, setLoading] = useState(false)
  const [editingChatId, setEditingChatId] = useState(null)
  const [editingTitle, setEditingTitle] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const activeChat = useMemo(() => chats.find((c) => c.id === activeChatId), [chats, activeChatId])
  const canSend = Boolean(activeChatId) && question.trim().length > 0 && !loading

  useEffect(() => {
    if (!accessToken) return
    getMe(accessToken).then(setMe).catch(() => setMe(null))
  }, [accessToken])

  useEffect(() => {
    if (!accessToken) return
    getChats(accessToken)
      .then((data) => {
        setChats(data)
        if (data[0]) setActiveChatId(data[0].id)
      })
      .catch((err) => setError(err.message))
  }, [accessToken])

  useEffect(() => {
    if (!accessToken || !activeChatId) return
    getMessages(accessToken, activeChatId)
      .then((data) => setMessages(data))
      .catch((err) => setError(err.message))
  }, [accessToken, activeChatId])

  async function onCreateChat() {
    setError('')
    const chat = await createChat(accessToken)
    setChats((prev) => [chat, ...prev])
    setActiveChatId(chat.id)
    setMessages([])
  }

  async function onDeleteChat(chatId) {
    setError('')
    await deleteChat(accessToken, chatId)
    const next = chats.filter((c) => c.id !== chatId)
    setChats(next)
    if (activeChatId === chatId) {
      setActiveChatId(next[0]?.id || null)
      setMessages([])
    }
  }

  function startRename(chat) {
    setEditingChatId(chat.id)
    setEditingTitle(chat.title)
  }

  async function onSaveRename(chatId) {
    const title = editingTitle.trim()
    if (!title || title.length > 80) return
    setError('')
    const updated = await renameChat(accessToken, chatId, title)
    setChats((prev) => prev.map((chat) => (chat.id === chatId ? updated : chat)))
    if (activeChatId === chatId) {
      setActiveChatId(updated.id)
    }
    setEditingChatId(null)
    setEditingTitle('')
  }

  function onQuestionKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (canSend) onSend()
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
    setError('')
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
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-head">
          <h2>Chats</h2>
          <ThemeToggle theme={theme} onToggle={toggleTheme} />
        </div>
        <button onClick={onCreateChat}>New chat</button>
        <button onClick={onLogout} className="secondary">Logout</button>
        <div className="chat-list">
          {chats.map((chat) => (
            <div key={chat.id} className={`chat-item ${activeChatId === chat.id ? 'active' : ''}`}>
              {editingChatId === chat.id ? (
                <>
                  <input
                    value={editingTitle}
                    onChange={(e) => setEditingTitle(e.target.value)}
                    maxLength={80}
                    className="chat-title-input"
                  />
                  <button className="tiny" onClick={() => onSaveRename(chat.id)}>Save</button>
                  <button className="tiny secondary" onClick={() => setEditingChatId(null)}>Cancel</button>
                </>
              ) : (
                <>
                  <button className="chat-select" onClick={() => setActiveChatId(chat.id)}>{chat.title}</button>
                  <button className="tiny" onClick={() => startRename(chat)}>Rename</button>
                  <button className="tiny danger" onClick={() => onDeleteChat(chat.id)}>Delete</button>
                </>
              )}
            </div>
          ))}
        </div>
      </aside>
      <main className="main">
        <header className="main-head">
          <h2>{activeChat?.title || 'Select a chat'}</h2>
          <div className="user-chip">{me ? `@${me.username}` : 'Guest'}</div>
        </header>
        <div className="messages">
          {messages.map((m) => (
            <div key={m.id} className={`message ${m.role}`}>
              <strong>{m.role === 'user' ? 'You' : 'Assistant'}:</strong> {m.content}
            </div>
          ))}
        </div>
        <div className="input-bar">
          <textarea
            value={question}
            onKeyDown={onQuestionKeyDown}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask anything... (Enter to send, Shift+Enter for a new line)"
          />
          <label>
            <input type="checkbox" checked={stream} onChange={(e) => setStream(e.target.checked)} /> Stream
          </label>
          <button onClick={onSend} className={canSend ? 'ready' : ''} disabled={!canSend}>{loading ? 'Loading...' : 'Send'}</button>
        </div>
        {error && <p className="error">{error}</p>}
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
  const [theme, setTheme] = useState(() => {
    if (typeof window === 'undefined') return 'dark'
    return localStorage.getItem('theme') || 'dark'
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [theme])

  function toggleTheme() {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))
  }

  return (
    <Routes>
      <Route path="/auth" element={<AuthPage theme={theme} toggleTheme={toggleTheme} />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <ChatPage theme={theme} toggleTheme={toggleTheme} />
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
