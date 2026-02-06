import { useState, useEffect } from 'react'
import { Link, useParams, useNavigate } from 'react-router-dom'
import { getChildren, getGameActions, gameInteraction } from '../api'
import ChildCards from '../components/ChildCards'
import GameScene from '../components/GameScene'
import paperIcon from '../../icons/paper.png'
import batteryIcon from '../../icons/battery.avif'
import trashIcon from '../../icons/trash.png'
import kranIcon from '../../icons/kran.avif'
import capsIcon from '../../icons/caps.png'

const ACTION_ICONS = {
  crane: { icon: '🚿', iconImage: kranIcon, hint: 'Закрыл кран' },
  cardboard_box: { icon: '📦', iconImage: paperIcon, hint: 'Принёс в сад макулатуру' },
  battery: { icon: '🔋', iconImage: batteryIcon, hint: 'Принёс и сдал батарейку' },
  plastic_cap: { icon: '🧴', iconImage: capsIcon, hint: 'Принёс и сдал крышки' },
  sorting: { icon: '🗑️', iconImage: trashIcon, hint: 'Дома сортировал мусор' },
}

export default function Play() {
  const { groupId } = useParams()
  const navigate = useNavigate()
  const [children, setChildren] = useState([])
  const [actions, setActions] = useState([])
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const childrenInGroup = groupId
    ? children.filter((c) => c.groupId === groupId)
    : []

  useEffect(() => {
    Promise.all([getChildren(), getGameActions()])
      .then(([childrenData, actionsData]) => {
        setChildren(childrenData)
        const merged = (actionsData || []).map((a) => ({
          ...a,
          ...ACTION_ICONS[a.id],
        }))
        setActions(merged)
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const selectedChild = selected ? children.find((c) => c.id === selected) : null

  const onInteraction = async (actionId) => {
    if (!selected) return
    try {
      const result = await gameInteraction(selected, actionId)
      if (result.success) {
        setChildren((prev) =>
          prev.map((c) => (c.id === selected ? { ...c, balance: result.new_balance } : c))
        )
        return { success: true, credited: result.credited }
      }
      return { success: false, reason: result.reason }
    } catch (e) {
      return { success: false, reason: 'error' }
    }
  }

  const goBackToGroups = () => navigate('/')
  const goBackToChildren = () => setSelected(null)

  if (loading) return <div className="page-loading">Загрузка...</div>
  if (error) return <div className="page-error">Ошибка: {error}</div>
  if (!groupId) return <div className="page-error">Группа не выбрана</div>

  return (
    <main className="home">
      <header className="home-header">
        <Link className="admin-link" to="/admin-login">
          Администратор
        </Link>
        <div className="home-title">
          <h1>Эко-сад</h1>
          <p className="subtitle">
            {!selected ? 'Выбери себя и играй' : selectedChild?.fullName}
          </p>
        </div>
      </header>

      {!selected ? (
        <>
          <div className="play-back-bar">
            <button
              type="button"
              className="btn-back"
              onClick={goBackToGroups}
              aria-label="Назад к группам"
            >
              ← Группы
            </button>
            <Link
              to={`/our-tree?group=${encodeURIComponent(groupId || '')}`}
              className="btn-tree-link"
            >
              Наше дерево
            </Link>
          </div>
          <ChildCards children={childrenInGroup} onSelect={setSelected} />
        </>
      ) : (
        <div className="game-wrap">
          <div className="balance-bar">
            <span className="balance-label">Экоши</span>
            <span className="balance-value">{selectedChild?.balance ?? 0}</span>
            <button
              type="button"
              className="btn-back"
              onClick={goBackToChildren}
              aria-label="Назад к выбору ребёнка"
            >
              ← Назад
            </button>
          </div>
          <GameScene onInteraction={onInteraction} actions={actions} />
        </div>
      )}
    </main>
  )
}
