import { useEffect, useState } from 'react';
import { Bell, Check, Clock, AlertTriangle } from 'lucide-react';
import './AlertManagement.css';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:3001';

function AlertManagement() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/alerts`);
        const data = await res.json();
        setAlerts(data.alerts || []);
      } catch (err) {
        console.error('Failed to fetch alerts:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAlerts();
    const interval = setInterval(fetchAlerts, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleAcknowledge = async (alertId) => {
    try {
      await fetch(`${API_BASE}/api/alerts/acknowledge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ alertId, acknowledgedBy: 'user' })
      });
      setAlerts(prev => prev.map(a =>
        a.id === alertId ? { ...a, status: 'acknowledged' } : a
      ));
    } catch (err) {
      console.error('Failed to acknowledge:', err);
    }
  };

  const filteredAlerts = filter === 'all'
    ? alerts
    : alerts.filter(a => a.status === filter);

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'critical': return <AlertTriangle className="icon-critical" size={18} />;
      case 'high': return <Bell className="icon-high" size={18} />;
      default: return <Bell className="icon-medium" size={18} />;
    }
  };

  if (loading) {
    return <div className="loading">Loading alerts...</div>;
  }

  return (
    <div className="alert-management">
      <div className="page-header">
        <h1>Alert Management</h1>
        <div className="filter-tabs">
          {['all', 'active', 'acknowledged'].map(f => (
            <button
              key={f}
              className={`filter-tab ${filter === f ? 'active' : ''}`}
              onClick={() => setFilter(f)}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="alerts-list">
        {filteredAlerts.length === 0 ? (
          <div className="no-alerts">No alerts found</div>
        ) : (
          filteredAlerts.map(alert => (
            <div key={alert.id} className={`alert-card ${alert.severity}`}>
              <div className="alert-header">
                {getSeverityIcon(alert.severity)}
                <span className="alert-type">{alert.type}</span>
                <span className={`alert-status ${alert.status}`}>
                  {alert.status === 'acknowledged' ? <Check size={14} /> : <Clock size={14} />}
                  {alert.status}
                </span>
              </div>

              <div className="alert-body">
                <div className="alert-rule">{alert.rule}</div>
                <div className="alert-details">
                  <span>IP: {alert.sourceIP}</span>
                  <span>Score: {alert.score}</span>
                  <span>Action: {alert.action}</span>
                </div>
              </div>

              <div className="alert-footer">
                <span className="alert-time">
                  {new Date(alert.timestamp).toLocaleString()}
                </span>
                {alert.status === 'active' && (
                  <button
                    className="ack-button"
                    onClick={() => handleAcknowledge(alert.id)}
                  >
                    Acknowledge
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default AlertManagement;
