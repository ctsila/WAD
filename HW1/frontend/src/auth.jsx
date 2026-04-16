/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { refreshToken as refreshTokenApi } from '../api/auth'

const AuthContext = createContext(null)

function parseJwt(token) {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [accessToken, setAccessToken] = useState(null)
  const [refreshToken, setRefreshToken] = useState(null)
  const [expiresAt, setExpiresAt] = useState(null)

  const setTokens = (access, refresh = null) => {
    setAccessToken(access)
    if (refresh !== null) setRefreshToken(refresh)
    const payload = parseJwt(access)
    setExpiresAt(payload?.exp ? payload.exp * 1000 : null)
  }

  const clearTokens = () => {
    setAccessToken(null)
    setRefreshToken(null)
    setExpiresAt(null)
  }

  useEffect(() => {
    if (!refreshToken || !expiresAt) return
    const timer = setInterval(async () => {
      const shouldRefresh = Date.now() > expiresAt - 60_000
      if (shouldRefresh) {
        try {
          const data = await refreshTokenApi(refreshToken)
          if (data?.access_token) setTokens(data.access_token)
        } catch {
          clearTokens()
        }
      }
    }, 30_000)
    return () => clearInterval(timer)
  }, [refreshToken, expiresAt])

  const value = useMemo(
    () => ({ accessToken, refreshToken, setTokens, clearTokens, isAuthenticated: Boolean(accessToken) }),
    [accessToken, refreshToken],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}
