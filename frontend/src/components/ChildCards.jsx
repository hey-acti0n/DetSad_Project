export default function ChildCards({ children, onSelect }) {
  return (
    <div className="child-cards">
      {children.map((child) => (
        <button
          key={child.id}
          type="button"
          className="child-card"
          onClick={() => onSelect(child.id)}
        >
          <span className="child-avatar">{child.fullName?.charAt(0) || '?'}</span>
          <span className="child-name">{child.fullName}</span>
          <span className="child-coins">🪙 {child.balance}</span>
        </button>
      ))}
    </div>
  )
}
