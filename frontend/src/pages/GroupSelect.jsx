import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getGroups } from '../api'

export default function GroupSelect() {
  const [groups, setGroups] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    getGroups()
      .then(setGroups)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const onSelectGroup = (groupId) => {
    navigate(`/play/${encodeURIComponent(groupId)}`)
  }

  if (loading) return <div className="page-loading">Загрузка...</div>
  if (error) return <div className="page-error">Ошибка: {error}</div>

  return (
    <main className="group-select">
      <header className="home-header">
        <Link className="admin-link" to="/admin-login">
          Администратор
        </Link>
        <div className="home-title">
          <h1>Эко-сад</h1>
          <p className="subtitle">Выбери свою группу</p>
        </div>
      </header>

      <div className="group-cards">
        {groups.map((group) => (
          <button
            key={group.id}
            type="button"
            className="group-card"
            onClick={() => onSelectGroup(group.id)}
          >
            <span className="group-number">{group.name}</span>
            <span className="group-label">Группа</span>
          </button>
        ))}
      </div>
    </main>
  )
}
