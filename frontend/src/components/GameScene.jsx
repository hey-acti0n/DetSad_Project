import { useState } from 'react'

export default function GameScene({ onInteraction, actions }) {
  const [feedback, setFeedback] = useState(null)
  const [disabled, setDisabled] = useState(false)
  const [craneClosed, setCraneClosed] = useState(false)

  const handleClick = async (actionId) => {
    if (disabled) return
    setDisabled(true)
    setFeedback(null)
    if (actionId === 'crane') setCraneClosed(true)
    const result = await onInteraction(actionId)
    if (result.success) {
      setFeedback({ type: 'ok', coins: result.credited })
    } else {
      const msg = result.reason === 'cooldown' ? 'Подожди немного' : result.reason === 'daily_limit' ? 'Лимит на сегодня' : 'Попробуй позже'
      setFeedback({ type: 'fail', msg })
    }
    setTimeout(() => {
      setFeedback(null)
      setDisabled(false)
      setCraneClosed(false)
    }, 1500)
  }

  return (
    <div className="game-scene">
      <div className="game-objects">
        {actions.map((action) => (
          <button
            key={action.id}
            type="button"
            className={`game-obj game-obj-${action.id}${action.id === 'crane' && craneClosed ? ' crane-closed' : ''}`}
            onClick={() => handleClick(action.id)}
            disabled={disabled}
            title={action.hint || action.name}
            aria-label={action.name}
          >
            {action.iconImage ? (
              <img src={action.iconImage} alt="" className="game-obj-icon-img" />
            ) : (
              <span className="icon">{action.icon}</span>
            )}
            {action.id === 'crane' && !action.iconImage && (
              <span className="crane-water" aria-hidden>
                <span className="crane-water-stream" />
              </span>
            )}
            <span className="label">{action.name}</span>
          </button>
        ))}
      </div>
      {feedback && (
        <div className={`feedback ${feedback.type}`}>
          {feedback.type === 'ok' && <>+{feedback.coins} 🪙</>}
          {feedback.type === 'fail' && feedback.msg}
        </div>
      )}
    </div>
  )
}
