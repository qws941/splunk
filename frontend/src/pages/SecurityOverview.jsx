import { useEffect, useState } from 'react';
import { Shield, AlertTriangle, Activity, TrendingUp } from 'lucide-react';
import './SecurityOverview.css';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:3001';

function SecurityOverview() {
  const [stats, setStats] = useState(null);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, eventsRes] = await Promise.all([
          fetch(`${API_BASE}/api/stats`),
          fetch(`${API_BASE}/api/events?limit=10`)
        ]);

        const statsData = await statsRes.json();
        const eventsData = await eventsRes.json();

        setStats(statsData);
        setEvents(eventsData.events || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div className="security-loading">Loading security data...</div>;
  }

  if (error) {
    return <div className="security-error">Error: {error}</div>;
  }

  const connections = stats?.connections || {};
  const processor = stats?.processor || {};

  return (
    <div className="security-overview">
      <h1 className="page-title">Security Overview</h1>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">
            <Shield size={24} />
          </div>
          <div className="stat-content">
            <span className="stat-value">{processor.processedCount || 0}</span>
            <span className="stat-label">Events Processed</span>
          </div>
        </div>

        <div className="stat-card critical">
          <div className="stat-icon">
            <AlertTriangle size={24} />
          </div>
          <div className="stat-content">
            <span className="stat-value">{processor.criticalEvents || 0}</span>
            <span className="stat-label">Critical Events</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">
            <Activity size={24} />
          </div>
          <div className="stat-content">
            <span className="stat-value">{connections.websocket || 0}</span>
            <span className="stat-label">Active Connections</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">
            <TrendingUp size={24} />
          </div>
          <div className="stat-content">
            <span className="stat-value">{processor.eventsPerMinute || 0}</span>
            <span className="stat-label">Events/min</span>
          </div>
        </div>
      </div>

      <div className="connections-status">
        <h2>System Connections</h2>
        <div className="connection-list">
          <div className={`connection-item ${connections.fortianalyzer ? 'connected' : 'disconnected'}`}>
            <span className="connection-dot"></span>
            <span>FortiAnalyzer</span>
          </div>
          <div className={`connection-item ${connections.splunk ? 'connected' : 'disconnected'}`}>
            <span className="connection-dot"></span>
            <span>Splunk</span>
          </div>
          <div className={`connection-item ${connections.slack ? 'connected' : 'disconnected'}`}>
            <span className="connection-dot"></span>
            <span>Slack</span>
          </div>
        </div>
      </div>

      <div className="recent-events">
        <h2>Recent Events</h2>
        <div className="events-table">
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Type</th>
                <th>Source</th>
                <th>Severity</th>
              </tr>
            </thead>
            <tbody>
              {events.length === 0 ? (
                <tr><td colSpan={4} className="no-data">No recent events</td></tr>
              ) : (
                events.map((event, i) => (
                  <tr key={event.id || i}>
                    <td>{new Date(event.timestamp || Date.now()).toLocaleTimeString()}</td>
                    <td>{event.type || 'unknown'}</td>
                    <td>{event.srcip || event.sourceIP || '-'}</td>
                    <td className={`severity-${event.severity || 'info'}`}>
                      {event.severity || 'info'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default SecurityOverview;
