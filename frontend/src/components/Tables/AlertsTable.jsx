import { format } from 'date-fns';
import './AlertsTable.css';

function AlertsTable({ alerts }) {
  const getSeverityColor = (severity) => {
    const colors = {
      critical: '#ef4444',
      high: '#f59e0b',
      medium: '#eab308',
      low: '#3b82f6'
    };
    return colors[severity] || '#888';
  };

  if (!alerts || alerts.length === 0) {
    return (
      <div className="empty-state">
        <p>No alerts to display</p>
      </div>
    );
  }

  return (
    <div className="alerts-table">
      {alerts.map((alert) => (
        <div key={alert.id} className="alert-row">
          <div className="alert-severity">
            <span
              className="severity-badge"
              style={{ background: getSeverityColor(alert.severity) }}
            >
              {alert.severity}
            </span>
          </div>
          <div className="alert-details">
            <div className="alert-rule">{alert.rule}</div>
            <div className="alert-meta">
              <span>{alert.sourceIP}</span>
              <span>•</span>
              <span>Score: {alert.score}</span>
              <span>•</span>
              <span>{format(new Date(alert.timestamp), 'HH:mm:ss')}</span>
            </div>
          </div>
          <div className="alert-action">
            <span className={`action-badge ${alert.action.toLowerCase().replace('_', '-')}`}>
              {alert.action}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}

export default AlertsTable;
