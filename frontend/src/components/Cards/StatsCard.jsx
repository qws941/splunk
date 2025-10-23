import './StatsCard.css';

function StatsCard({ title, value, trend, trendUp, icon, variant = 'default' }) {
  return (
    <div className={`stats-card ${variant}`}>
      <div className="stats-card-header">
        <span className="stats-icon">{icon}</span>
        <span className={`stats-trend ${trendUp ? 'up' : 'down'}`}>
          {trendUp ? '↑' : '↓'} {trend}
        </span>
      </div>
      <div className="stats-card-body">
        <div className="stats-value">{value.toLocaleString()}</div>
        <div className="stats-title">{title}</div>
      </div>
    </div>
  );
}

export default StatsCard;
