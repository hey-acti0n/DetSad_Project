import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  adminCheckAuth,
  adminLogout,
  adminMe,
  adminStatsGroups,
  adminStatsChildren,
  adminChildEvents,
  adminEvents,
  adminBalanceAdjust,
  adminMonthlyResults,
  adminGroupCreate,
  adminGroupUpdate,
  adminGroupDelete,
  adminChildCreate,
  adminChildUpdate,
  adminChildDelete,
} from '../api'

const MONTH_NAMES = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']

function defaultPeriod() {
  const now = new Date()
  const weekAgo = new Date(now)
  weekAgo.setDate(weekAgo.getDate() - 7)
  return {
    from: weekAgo.toISOString().slice(0, 10),
    to: now.toISOString().slice(0, 10),
  }
}

export default function AdminPanel() {
  const [auth, setAuth] = useState(null)
  const [activeTab, setActiveTab] = useState('groups')
  const [period, setPeriod] = useState(defaultPeriod)
  const [groups, setGroups] = useState([])
  const [children, setChildren] = useState([])
  const [events, setEvents] = useState([])
  const [childDetail, setChildDetail] = useState(null)
  const [childEvents, setChildEvents] = useState([])
  const [filterGroup, setFilterGroup] = useState('')
  const [filterQ, setFilterQ] = useState('')
  const [loading, setLoading] = useState(false)
  const [groupForm, setGroupForm] = useState(null)
  const [childForm, setChildForm] = useState(null)
  const [ratingChildren, setRatingChildren] = useState([])
  const [ratingLoading, setRatingLoading] = useState(false)
  const [monthlyResults, setMonthlyResults] = useState([])
  const [monthlyLoading, setMonthlyLoading] = useState(false)
  const [me, setMe] = useState(null)
  const navigate = useNavigate()
  const isEducator = me?.role === 'educator'

  const refetch = () => {
    setLoading(true)
    return Promise.all([
      adminStatsGroups(period.from, period.to),
      adminStatsChildren(filterGroup || undefined, filterQ || undefined, period.from, period.to),
      adminEvents(filterGroup || undefined, undefined, period.from, period.to),
    ])
      .then(([g, c, e]) => {
        setGroups(g)
        setChildren(c)
        setEvents(e)
        return [g, c, e]
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    adminCheckAuth().then((ok) => {
      if (!ok) navigate('/admin-login', { replace: true })
      else setAuth(true)
    })
  }, [navigate])

  useEffect(() => {
    if (!auth) return
    adminMe().then(setMe).catch(() => setMe({ role: 'admin', group_id: null }))
  }, [auth])

  useEffect(() => {
    if (!auth) return
    refetch()
  }, [auth, period, filterGroup, filterQ])

  useEffect(() => {
    if (!childDetail) {
      setChildEvents([])
      return
    }
    adminChildEvents(childDetail.id, period.from, period.to).then(setChildEvents)
  }, [childDetail, period])

  useEffect(() => {
    if (!auth || activeTab !== 'rating') return
    setRatingLoading(true)
    adminStatsChildren(undefined, undefined, period.from, period.to)
      .then((list) => {
        const sorted = [...list].sort((a, b) => (b.balance || 0) - (a.balance || 0))
        setRatingChildren(sorted)
      })
      .finally(() => setRatingLoading(false))
  }, [auth, activeTab, period.from, period.to])

  useEffect(() => {
    if (!auth || activeTab !== 'monthly') return
    setMonthlyLoading(true)
    adminMonthlyResults()
      .then(setMonthlyResults)
      .finally(() => setMonthlyLoading(false))
  }, [auth, activeTab])

  const handleLogout = () => {
    adminLogout().then(() => navigate('/', { replace: true }))
  }

  const handleBalanceAdjust = async (childId, delta, comment) => {
    try {
      await adminBalanceAdjust(childId, delta, comment)
      const [, c] = await refetch() || []
      setChildDetail(c?.find((ch) => ch.id === childId) || null)
    } catch (err) {
      alert(err.message)
    }
  }

  const handleGroupSave = async (name, id) => {
    try {
      if (id) await adminGroupUpdate(id, name)
      else await adminGroupCreate(name)
      setGroupForm(null)
      refetch()
    } catch (err) {
      alert(err.message)
    }
  }

  const handleGroupDelete = async (id) => {
    if (!window.confirm('Удалить группу? В группе не должно быть детей.')) return
    try {
      await adminGroupDelete(id)
      setGroupForm(null)
      refetch()
    } catch (err) {
      alert(err.message)
    }
  }

  const handleChildSave = async (fullName, groupId, id) => {
    try {
      if (id) await adminChildUpdate(id, fullName, groupId)
      else await adminChildCreate(fullName, groupId)
      setChildForm(null)
      setChildDetail(null)
      refetch()
    } catch (err) {
      alert(err.message)
    }
  }

  const handleChildDelete = async (id) => {
    if (!window.confirm('Удалить ребёнка и всю его историю?')) return
    try {
      await adminChildDelete(id)
      setChildForm(null)
      setChildDetail(null)
      refetch()
    } catch (err) {
      alert(err.message)
    }
  }

  if (auth === null) return <div className="page-loading">Проверка входа...</div>

  return (
    <main className="admin-panel">
      <header className="admin-header">
        <h1>Панель администратора</h1>
        <button type="button" className="btn-logout" onClick={handleLogout}>
          Выйти
        </button>
      </header>

      <div className="admin-period">
        <label>
          С <input type="date" value={period.from} onChange={(e) => setPeriod((p) => ({ ...p, from: e.target.value }))} />
        </label>
        <label>
          По <input type="date" value={period.to} onChange={(e) => setPeriod((p) => ({ ...p, to: e.target.value }))} />
        </label>
      </div>

      <nav className="admin-tabs">
        <button type="button" className={activeTab === 'groups' ? 'active' : ''} onClick={() => setActiveTab('groups')}>
          Группы
        </button>
        <button type="button" className={activeTab === 'children' ? 'active' : ''} onClick={() => setActiveTab('children')}>
          Дети
        </button>
        <button type="button" className={activeTab === 'rating' ? 'active' : ''} onClick={() => setActiveTab('rating')}>
          Рейтинг
        </button>
        <button type="button" className={activeTab === 'events' ? 'active' : ''} onClick={() => setActiveTab('events')}>
          События
        </button>
        <button type="button" className={activeTab === 'monthly' ? 'active' : ''} onClick={() => setActiveTab('monthly')}>
          Итоги по месяцам
        </button>
      </nav>

      {loading && <p className="loading">Загрузка...</p>}

      {activeTab === 'groups' && (
        <section className="admin-section">
          {!isEducator && (
            <div className="admin-section-header">
              <button type="button" className="btn-primary" onClick={() => setGroupForm({ mode: 'add', name: '' })}>
                + Добавить группу
              </button>
            </div>
          )}
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Группа</th>
                  <th>Детей</th>
                  <th>Суммарный баланс</th>
                  <th>Начислено за период</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {groups.map((g) => (
                <tr key={g.groupId}>
                  <td>{g.groupName}</td>
                  <td>{g.childrenCount}</td>
                  <td>{g.totalBalance}</td>
                  <td>{g.periodCredited}</td>
                  <td>
                    <button type="button" className="btn-sm" onClick={() => setGroupForm({ mode: 'edit', id: g.groupId, name: g.groupName })}>Изменить</button>
                    {!isEducator && (
                      <>
                        {' '}
                        <button type="button" className="btn-sm btn-danger" onClick={() => handleGroupDelete(g.groupId)}>Удалить</button>
                      </>
                    )}
                  </td>
                </tr>
                ))}
              </tbody>
            </table>
          </div>
          {groupForm && (
            <div className="modal-overlay" onClick={() => setGroupForm(null)}>
              <div className="modal-card" onClick={(e) => e.stopPropagation()}>
                <h3>{groupForm.mode === 'add' ? 'Новая группа' : 'Редактировать группу'}</h3>
                <GroupForm
                  initialName={groupForm.name}
                  initialId={groupForm.mode === 'edit' ? groupForm.id : null}
                  onSave={handleGroupSave}
                  onCancel={() => setGroupForm(null)}
                />
              </div>
            </div>
          )}
        </section>
      )}

      {activeTab === 'rating' && (
        <section className="admin-section">
          <h2 className="admin-section-title">Рейтинг по количеству очков</h2>
          {ratingLoading && <p className="loading">Загрузка...</p>}
          {!ratingLoading && (
            <div className="admin-table-wrap">
              <table className="admin-table admin-table-rating">
                <thead>
                  <tr>
                    <th>Место</th>
                    <th>ФИО</th>
                    <th>Группа</th>
                    <th>Очки</th>
                  </tr>
                </thead>
                <tbody>
                  {ratingChildren.map((c, index) => (
                    <tr key={c.id}>
                      <td className="rating-place">{index + 1}</td>
                      <td>{c.fullName}</td>
                      <td>{c.groupName || c.groupId}</td>
                      <td className="rating-points">{c.balance ?? 0}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {!ratingLoading && ratingChildren.length === 0 && (
            <p className="admin-empty">Нет данных для рейтинга</p>
          )}
        </section>
      )}

      {activeTab === 'children' && (
        <section className="admin-section">
          <div className="admin-filters">
            <button type="button" className="btn-primary" onClick={() => setChildForm({ mode: 'add', fullName: '', groupId: '' })}>
              + Добавить ребёнка
            </button>
            <input
              type="text"
              placeholder="Поиск по ФИО"
              value={filterQ}
              onChange={(e) => setFilterQ(e.target.value)}
            />
            <select value={filterGroup} onChange={(e) => setFilterGroup(e.target.value)}>
              <option value="">Все группы</option>
              {groups.map((g) => (
                <option key={g.groupId} value={g.groupId}>
                  {g.groupName}
                </option>
              ))}
            </select>
          </div>
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>ФИО</th>
                  <th>Группа</th>
                  <th>Баланс</th>
                  <th>Начислено за период</th>
                  <th>Действий</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {children.map((c) => (
                  <tr key={c.id}>
                    <td>{c.fullName}</td>
                    <td>{c.groupName || c.groupId}</td>
                    <td>{c.balance}</td>
                    <td>{c.periodCredited}</td>
                    <td>{c.actionsCount}</td>
                    <td>
                      <button type="button" className="btn-sm" onClick={() => setChildDetail(c)}>Карточка</button>
                      {' '}
                      <button type="button" className="btn-sm" onClick={() => setChildForm({ mode: 'edit', id: c.id, fullName: c.fullName, groupId: c.groupId || '' })}>Изменить</button>
                      {' '}
                      <button type="button" className="btn-sm btn-danger" onClick={() => handleChildDelete(c.id)}>Удалить</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {childForm && (
            <div className="modal-overlay" onClick={() => setChildForm(null)}>
              <div className="modal-card" onClick={(e) => e.stopPropagation()}>
                <h3>{childForm.mode === 'add' ? 'Новый ребёнок' : 'Редактировать ребёнка'}</h3>
                <ChildForm
                  initialFullName={childForm.fullName}
                  initialGroupId={childForm.groupId}
                  initialId={childForm.mode === 'edit' ? childForm.id : null}
                  groups={groups}
                  onSave={handleChildSave}
                  onCancel={() => setChildForm(null)}
                />
              </div>
            </div>
          )}
          {childDetail && (
            <div className="child-detail-modal" onClick={() => setChildDetail(null)}>
              <div className="child-detail-card" onClick={(e) => e.stopPropagation()}>
                <button
                  type="button"
                  className="modal-close-x"
                  onClick={() => setChildDetail(null)}
                  aria-label="Закрыть"
                  title="Закрыть"
                >
                  ×
                </button>
                <h3>{childDetail.fullName}</h3>
                <p>Баланс: {childDetail.balance}</p>
                <BalanceAdjustForm childId={childDetail.id} onAdjust={handleBalanceAdjust} />
                <h4>История за период</h4>
                <table className="admin-table small">
                  <thead>
                    <tr>
                      <th>Действие</th>
                      <th>Экошей</th>
                      <th>Время</th>
                    </tr>
                  </thead>
                  <tbody>
                    {childEvents.map((e) => (
                      <tr key={e.id}>
                        <td>{e.actionName || e.actionId}</td>
                        <td>{e.credited}</td>
                        <td>{e.timestamp ? new Date(e.timestamp).toLocaleString('ru') : ''}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <button type="button" className="btn-close" onClick={() => setChildDetail(null)}>
                  Закрыть
                </button>
              </div>
            </div>
          )}
        </section>
      )}

      {activeTab === 'monthly' && (
        <section className="admin-section">
          <h2 className="admin-section-title">Итоги по месяцам (баланс обнуляется в конце каждого месяца)</h2>
          {monthlyLoading && <p className="loading">Загрузка...</p>}
          {!monthlyLoading && monthlyResults.length === 0 && (
            <p className="admin-empty">Пока нет сохранённых итогов. Итоги появятся после первого перехода в новый месяц.</p>
          )}
          {!monthlyLoading && monthlyResults.length > 0 && (() => {
            const childList = []
            const seen = new Set()
            monthlyResults.forEach((row) => {
              (row.children || []).forEach((ch) => {
                if (!seen.has(ch.childId)) {
                  seen.add(ch.childId)
                  childList.push(ch)
                }
              })
            })
            return (
              <div className="admin-table-wrap">
                <table className="admin-table admin-table-monthly">
                  <thead>
                    <tr>
                      <th>Месяц</th>
                      {childList.map((ch) => (
                        <th key={ch.childId}>{ch.fullName || ch.childId}</th>
                      ))}
                      <th>Всего Экошей</th>
                    </tr>
                  </thead>
                  <tbody>
                    {monthlyResults.map((row, idx) => {
                      const childMap = Object.fromEntries((row.children || []).map((ch) => [ch.childId, ch.balance]))
                      return (
                        <tr key={`${row.year}-${row.month}-${idx}`}>
                          <td>{MONTH_NAMES[(row.month || 1) - 1]} {row.year}</td>
                          {childList.map((ch) => (
                            <td key={ch.childId}>{childMap[ch.childId] ?? '—'}</td>
                          ))}
                          <td className="admin-monthly-total">{row.totalSum ?? 0}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )
          })()}
        </section>
      )}

      {activeTab === 'events' && (
        <section className="admin-section">
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Ребёнок</th>
                  <th>Действие</th>
                  <th>Экошей</th>
                  <th>Время</th>
                </tr>
              </thead>
              <tbody>
                {events.map((e) => (
                  <tr key={e.id}>
                    <td>{e.childName || e.childId}</td>
                    <td>{e.actionName || e.actionId}</td>
                    <td>{e.credited}</td>
                    <td>{e.timestamp ? new Date(e.timestamp).toLocaleString('ru') : ''}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </main>
  )
}

function GroupForm({ initialName, initialId, onSave, onCancel }) {
  const [name, setName] = useState(initialName || '')
  const submit = (e) => {
    e.preventDefault()
    if (!name.trim()) return
    onSave(name.trim(), initialId)
  }
  return (
    <form onSubmit={submit} className="admin-form">
      <label>
        Название группы
        <input type="text" value={name} onChange={(e) => setName(e.target.value)} required autoFocus />
      </label>
      <div className="form-actions">
        <button type="submit">Сохранить</button>
        <button type="button" className="btn-close" onClick={onCancel}>Отмена</button>
      </div>
    </form>
  )
}

function ChildForm({ initialFullName, initialGroupId, initialId, groups, onSave, onCancel }) {
  const [fullName, setFullName] = useState(initialFullName || '')
  const [groupId, setGroupId] = useState(initialGroupId || '')
  const submit = (e) => {
    e.preventDefault()
    if (!fullName.trim()) return
    onSave(fullName.trim(), groupId || null, initialId)
  }
  return (
    <form onSubmit={submit} className="admin-form">
      <label>
        ФИО
        <input type="text" value={fullName} onChange={(e) => setFullName(e.target.value)} required autoFocus />
      </label>
      <label>
        Группа
        <select value={groupId} onChange={(e) => setGroupId(e.target.value)}>
          <option value="">— не выбрана —</option>
          {groups.map((g) => (
            <option key={g.groupId} value={g.groupId}>{g.groupName}</option>
          ))}
        </select>
      </label>
      <div className="form-actions">
        <button type="submit">Сохранить</button>
        <button type="button" className="btn-close" onClick={onCancel}>Отмена</button>
      </div>
    </form>
  )
}

function BalanceAdjustForm({ childId, onAdjust }) {
  const [delta, setDelta] = useState('')
  const [comment, setComment] = useState('')
  const submit = (e) => {
    e.preventDefault()
    const d = parseInt(delta, 10)
    if (isNaN(d) || d === 0) return
    onAdjust(childId, d, comment)
    setDelta('')
    setComment('')
  }
  return (
    <form onSubmit={submit} className="balance-adjust-form">
      <label>
        Изменить на <input type="number" value={delta} onChange={(e) => setDelta(e.target.value)} placeholder="+5 или -3" />
      </label>
      <label>
        Комментарий <input type="text" value={comment} onChange={(e) => setComment(e.target.value)} />
      </label>
      <button type="submit">Применить</button>
    </form>
  )
}
