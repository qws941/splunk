import { useStore } from '../store/store';
import './Dashboard.css';

function SystemHealth() {
  const { stats, wsConnected } = useStore();

  return (
    <div className="dashboard-page">
      <div className="page-header">
        <h2>⚙️ System Health</h2>
        <p>Monitor system performance and component status</p>
      </div>

      <div className="stats-grid">
        <div className="dashboard-card">
          <h3>Connection Status</h3>
          <p>WebSocket: {wsConnected ? '✅ Connected' : '❌ Disconnected'}</p>
          <p>FortiAnalyzer: {stats?.connections?.fortianalyzer ? '✅' : '❌'}</p>
          <p>Splunk: {stats?.connections?.splunk ? '✅' : '❌'}</p>
          <p>Slack: {stats?.connections?.slack ? '✅' : '❌'}</p>
        </div>

        <div className="dashboard-card">
          <h3>Processing Stats</h3>
          <p>Processed: {stats?.processor?.processedCount || 0}</p>
          <p>Critical: {stats?.processor?.criticalEvents || 0}</p>
          <p>High: {stats?.processor?.highEvents || 0}</p>
          <p>Errors: {stats?.processor?.errorCount || 0}</p>
        </div>
      </div>
    </div>
  );
}

export default SystemHealth;
