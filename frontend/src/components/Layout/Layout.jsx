import { useStore } from '../../store/store';
import Sidebar from '../Sidebar/Sidebar';
import Breadcrumb from '../Breadcrumb/Breadcrumb';
import './Layout.css';

function Layout({ children }) {
  const { stats, wsConnected } = useStore();

  return (
    <div className="layout">
      <Sidebar />
      
      <div className="layout-main">
        <header className="header">
          <div className="header-left">
            <Breadcrumb />
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

        <main className="content">
          {children}
        </main>
      </div>
    </div>
  );
}

export default Layout;
