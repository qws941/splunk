import { useEffect } from 'react';
import { useStore } from '../store/store';
import './Dashboard.css';

function SecurityOverview() {
  const { events, fetchEvents } = useStore();

  useEffect(() => {
    fetchEvents({ limit: 100, timeRange: '-24h' });
  }, [fetchEvents]);

  return (
    <div className="dashboard-page">
      <div className="page-header">
        <h2>🛡️ Security Overview</h2>
        <p>Comprehensive security monitoring and threat detection</p>
      </div>

      <div className="dashboard-card">
        <h3>Security Events (Last 24h)</h3>
        <p>Total events: {events.length}</p>
        {/* TODO: Add detailed security visualizations */}
      </div>
    </div>
  );
}

export default SecurityOverview;
