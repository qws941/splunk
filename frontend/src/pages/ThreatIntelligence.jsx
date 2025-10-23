import { useEffect } from 'react';
import { useStore } from '../store/store';
import './Dashboard.css';

function ThreatIntelligence() {
  const { threats, fetchThreats } = useStore();

  useEffect(() => {
    fetchThreats();
  }, [fetchThreats]);

  return (
    <div className="dashboard-page">
      <div className="page-header">
        <h2>🎯 Threat Intelligence</h2>
        <p>Threat analysis and geolocation insights</p>
      </div>

      <div className="dashboard-card">
        <h3>Top Threats</h3>
        {threats?.topThreats?.map((threat, idx) => (
          <div key={idx} style={{ padding: '1rem', background: '#2a2a2a', marginBottom: '1rem', borderRadius: '8px' }}>
            <h4>{threat.ip} ({threat.country})</h4>
            <p>Abuse Score: {threat.abuseScore} | Events: {threat.eventCount}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ThreatIntelligence;
