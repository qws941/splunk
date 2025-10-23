import { useEffect } from 'react';
import { useStore } from '../store/store';
import AlertsTable from '../components/Tables/AlertsTable';
import './Dashboard.css';

function AlertManagement() {
  const { alerts, fetchAlerts } = useStore();

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  return (
    <div className="dashboard-page">
      <div className="page-header">
        <h2>🚨 Alert Management</h2>
        <p>Monitor and manage security alerts</p>
      </div>

      <div className="dashboard-card">
        <AlertsTable alerts={alerts} />
      </div>
    </div>
  );
}

export default AlertManagement;
