import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard';
import SecurityOverview from './pages/SecurityOverview';
import CorrelationAnalysis from './pages/CorrelationAnalysis';
import AlertManagement from './pages/AlertManagement';
import ThreatIntelligence from './pages/ThreatIntelligence';
import SystemHealth from './pages/SystemHealth';
import { useWebSocket } from './hooks/useWebSocket';
import { useStore } from './store/store';

function App() {
  const { connect, disconnect } = useWebSocket();
  const { fetchStats } = useStore();

  useEffect(() => {
    // Connect to WebSocket
    connect();

    // Fetch initial stats
    fetchStats();

    // Poll stats every 30 seconds
    const interval = setInterval(() => {
      fetchStats();
    }, 30000);

    return () => {
      disconnect();
      clearInterval(interval);
    };
  }, [connect, disconnect, fetchStats]);

  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/security" element={<SecurityOverview />} />
          <Route path="/correlation" element={<CorrelationAnalysis />} />
          <Route path="/alerts" element={<AlertManagement />} />
          <Route path="/threats" element={<ThreatIntelligence />} />
          <Route path="/system" element={<SystemHealth />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
