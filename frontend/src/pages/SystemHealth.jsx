import { useEffect, useState } from 'react';
import { Activity, Server, Database, Wifi, RefreshCw } from 'lucide-react';
import './SystemHealth.css';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:3001';

function SystemHealth() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchHealth = async () => {
    try {
      const res = await fetch(`${API_BASE}/health`);
      const data = await res.json();
      setHealth(data);
    } catch (err) {
      console.error('Failed to fetch health:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchHealth();
  };

  if (loading) {
    return <div className="loading">Loading system health...</div>;
  }

  const services = health?.services || {};
  const uptime = health?.uptime || 0;

  const formatUptime = (seconds) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    if (days > 0) return `${days}d ${hours}h ${mins}m`;
    if (hours > 0) return `${hours}h ${mins}m`;
    return `${mins}m`;
  };

  const serviceList = [
    { key: 'faz', name: 'FortiAnalyzer', icon: Server },
    { key: 'splunk', name: 'Splunk HEC', icon: Database },
    { key: 'slack', name: 'Slack Webhook', icon: Wifi },
    { key: 'processor', name: 'Event Processor', icon: Activity },
  ];

  return (
    <div className="system-page">
      <div className="page-header">
        <div>
          <h1>System Health</h1>
          <p className="page-subtitle">Monitor service status and system metrics</p>
        </div>
        <button className="refresh-btn" onClick={handleRefresh} disabled={refreshing}>
          <RefreshCw size={18} className={refreshing ? 'spinning' : ''} />
          Refresh
        </button>
      </div>

      <div className="uptime-banner">
        <Activity size={24} />
        <div>
          <span className="uptime-label">System Uptime</span>
          <span className="uptime-value">{formatUptime(uptime)}</span>
        </div>
        <span className={`status-badge ${health?.status === 'healthy' ? 'healthy' : 'degraded'}`}>
          {health?.status || 'unknown'}
        </span>
      </div>

      <section className="section">
        <h2>Service Status</h2>
        <div className="services-grid">
          {serviceList.map(({ key, name, icon: Icon }) => {
            const service = services[key] || { connected: false };
            const isConnected = service.connected || service.status === 'active';
            
            return (
              <div key={key} className={`service-card ${isConnected ? 'connected' : 'disconnected'}`}>
                <div className="service-icon">
                  <Icon size={24} />
                </div>
                <div className="service-info">
                  <span className="service-name">{name}</span>
                  <span className="service-status">
                    <span className="status-dot"></span>
                    {isConnected ? 'Connected' : 'Disconnected'}
                  </span>
                </div>
                {service.lastCheck && (
                  <span className="last-check">
                    Last: {new Date(service.lastCheck).toLocaleTimeString()}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </section>

      <section className="section">
        <h2>System Metrics</h2>
        <div className="metrics-grid">
          <div className="metric-card">
            <span className="metric-label">Memory Usage</span>
            <div className="metric-bar">
              <div className="metric-fill" style={{ width: `${health?.memory?.percent || 0}%` }} />
            </div>
            <span className="metric-value">{health?.memory?.percent || 0}%</span>
          </div>
          <div className="metric-card">
            <span className="metric-label">CPU Usage</span>
            <div className="metric-bar">
              <div className="metric-fill" style={{ width: `${health?.cpu?.percent || 0}%` }} />
            </div>
            <span className="metric-value">{health?.cpu?.percent || 0}%</span>
          </div>
          <div className="metric-card">
            <span className="metric-label">Event Queue</span>
            <div className="metric-bar">
              <div 
                className="metric-fill" 
                style={{ width: `${Math.min(100, (health?.queue?.size || 0) / 10)}%` }} 
              />
            </div>
            <span className="metric-value">{health?.queue?.size || 0}</span>
          </div>
        </div>
      </section>
    </div>
  );
}

export default SystemHealth;
