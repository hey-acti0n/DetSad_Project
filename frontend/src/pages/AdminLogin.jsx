import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { adminLogin } from '../api'

export default function AdminLogin() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    fetch('/api/v1/csrf-set', { credentials: 'include' }).catch(() => {})
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await adminLogin(username, password)
      navigate('/admin', { replace: true })
    } catch (e) {
      setError(e.message === 'invalid_credentials' ? 'Неверный логин или пароль' : e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="admin-login-page">
      <div className="admin-login-card">
        <h1>Вход для администратора</h1>
        <form onSubmit={handleSubmit}>
          <label>
            Логин
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
            />
          </label>
          <label>
            Пароль
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </label>
          {error && <p className="form-error">{error}</p>}
          <button type="submit" disabled={loading}>
            {loading ? 'Вход...' : 'Войти'}
          </button>
        </form>
      </div>
    </main>
  )
}
