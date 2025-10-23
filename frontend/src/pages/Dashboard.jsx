import { useEffect } from 'react';
import { useStore } from '../store/store';
import StatsCard from '../components/Cards/StatsCard';
import EventsChart from '../components/Charts/EventsChart';
import AlertsTable from '../components/Tables/AlertsTable';
import './Dashboard.css';

function Dashboard() {
  const { stats, events, alerts, fetchEvents, fetchAlerts, loading } = useStore();

  useEffect(() => {
    fetchEvents({ limit: 50, timeRange: '-1h' });
    fetchAlerts();
  }, [fetchEvents, fetchAlerts]);

  const processorStats = stats?.processor || {};

  return (
    <div className="dashboard-page">
      <div className="page-header">
        <h2>Dashboard Overview</h2>
        <p>Real-time security monitoring and event analysis</p>
      </div>

      <div className="stats-grid">
        <StatsCard
          title="Total Events"
          value={processorStats.processedCount || 0}
          trend="+12%"
          trendUp={true}
          icon="📊"
        />
        <StatsCard
          title="Critical Events"
          value={processorStats.criticalEvents || 0}
          trend="-8%"
          trendUp={false}
          icon="🔴"
          variant="critical"
        />
        <StatsCard
          title="High Severity"
          value={processorStats.highEvents || 0}
          trend="+5%"
          trendUp={true}
          icon="🟠"
          variant="high"
        />
        <StatsCard
          title="Active Alerts"
          value={alerts?.filter(a => a.status === 'active').length || 0}
          trend="0%"
          trendUp={false}
          icon="🚨"
          variant="warning"
        />
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-card chart-card">
          <div className="card-header">
            <h3>Event Timeline (Last Hour)</h3>
            <span className="card-badge">Live</span>
          </div>
          <EventsChart events={events} />
        </div>

        <div className="dashboard-card">
          <div className="card-header">
            <h3>Recent Alerts</h3>
            <span className="card-count">{alerts?.length || 0}</span>
          </div>
          <AlertsTable alerts={alerts?.slice(0, 5) || []} />
        </div>
      </div>

      {loading && (
        <div className="loading-overlay">
          <div className="spinner"></div>
          <p>Loading data...</p>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
