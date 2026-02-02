import { useState, useEffect } from 'react'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import { getChildren } from '../api'
import tree1 from '../../icons/tree_1.avif'
import tree2 from '../../icons/tree_2.avif'
import tree3 from '../../icons/tree_3.avif'
import tree4 from '../../icons/tree_4.avif'

const TREE_SIZE_STAGE_1 = 100
const TREE_SIZE_MULTIPLIER = 1.8

const TREE_STAGE_THRESHOLDS = [200, 400, 600] // пороги для стадий 2, 3, 4 (монет)

function getTreeImage(totalCoins) {
  if (totalCoins < TREE_STAGE_THRESHOLDS[0]) return tree1
  if (totalCoins < TREE_STAGE_THRESHOLDS[1]) return tree2
  if (totalCoins < TREE_STAGE_THRESHOLDS[2]) return tree3
  return tree4
}

function getTreeSize(totalCoins) {
  const stage = totalCoins < TREE_STAGE_THRESHOLDS[0] ? 0
    : totalCoins < TREE_STAGE_THRESHOLDS[1] ? 1
    : totalCoins < TREE_STAGE_THRESHOLDS[2] ? 2
    : 3
  return Math.round(TREE_SIZE_STAGE_1 * TREE_SIZE_MULTIPLIER ** stage)
}

export default function OurTree() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const groupId = searchParams.get('group') || ''

  const [totalCoins, setTotalCoins] = useState(0)
  const [groupName, setGroupName] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!groupId) {
      navigate('/', { replace: true })
      return
    }
    getChildren()
      .then((children) => {
        const inGroup = (children || []).filter((c) => c.groupId === groupId)
        const total = inGroup.reduce((sum, c) => sum + (Number(c.balance) || 0), 0)
        setTotalCoins(total)
        const num = groupId.replace(/^group/, '') || groupId
        setGroupName(inGroup.length ? `Группа ${num}` : groupId)
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [groupId, navigate])

  const treeImage = getTreeImage(totalCoins)
  const treeSize = getTreeSize(totalCoins)

  if (!groupId) return null

  return (
    <main className="our-tree">
      <header className="home-header">
        <Link className="admin-link" to="/admin-login">
          Администратор
        </Link>
        <div className="home-title">
          <h1>Эко-сад</h1>
          <p className="subtitle">Наше дерево</p>
        </div>
      </header>

      <section className="tree-content">
        <h2>Наше дерево {groupName && `— ${groupName}`}</h2>
        {loading && <div className="page-loading">Загрузка...</div>}
        {error && <div className="page-error">Ошибка: {error}</div>}
        {!loading && !error && (
          <>
            <img
              src={treeImage}
              alt="Наше дерево"
              className="tree-image"
              style={{ width: treeSize, height: treeSize }}
            />
            <p className="tree-coins">Экошей в группе: {totalCoins}</p>
            <Link to="/" className="btn-back-link">
              ← Назад к игре
            </Link>
          </>
        )}
      </section>
    </main>
  )
}
