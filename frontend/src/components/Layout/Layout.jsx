import { Link, useLocation } from 'react-router-dom';
import { useStore } from '../../store/store';
import './Layout.css';

function Layout({ children }) {
  const location = useLocation();
  const { stats, wsConnected } = useStore();

  const navigation = [
    { path: '/dashboard', label: 'Dashboard', icon: '📊' },
    { path: '/security', label: 'Security', icon: '🛡️' },
    { path: '/correlation', label: 'Correlation', icon: '🔗' },
    { path: '/alerts', label: 'Alerts', icon: '🚨' },
    { path: '/threats', label: 'Threats', icon: '🎯' },
    { path: '/system', label: 'System', icon: '⚙️' }
  ];

  return (
    <div className="layout">
      <header className="header">
        <div className="header-left">
          <h1>🔐 FortiAnalyzer-Splunk Dashboard</h1>
        </div>
        <div className="header-right">
          <div className={`status-indicator ${wsConnected ? 'connected' : 'disconnected'}`}>
            <span className="status-dot"></span>
            <span>{wsConnected ? 'Connected' : 'Disconnected'}</span>
          </div>
          {stats && (
            <div className="header-stats">
              <div className="stat">
                <span className="stat-label">Processed:</span>
                <span className="stat-value">{stats.processor?.processedCount || 0}</span>
              </div>
              <div className="stat critical">
                <span className="stat-label">Critical:</span>
                <span className="stat-value">{stats.processor?.criticalEvents || 0}</span>
              </div>
            </div>
          )}
        </div>
      </header>

      <nav className="sidebar">
        {navigation.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`nav-link ${location.pathname === item.path ? 'active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </Link>
        ))}
      </nav>

      <main className="content">
        {children}
      </main>
    </div>
  );
}

export default Layout;
