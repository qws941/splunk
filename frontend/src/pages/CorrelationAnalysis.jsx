import { useEffect } from 'react';
import { useStore } from '../store/store';
import './Dashboard.css';

function CorrelationAnalysis() {
  const { correlation, fetchCorrelation } = useStore();

  useEffect(() => {
    fetchCorrelation('-24h');
  }, [fetchCorrelation]);

  return (
    <div className="dashboard-page">
      <div className="page-header">
        <h2>🔗 Correlation Analysis</h2>
        <p>Advanced event correlation and pattern detection</p>
      </div>

      <div className="dashboard-card">
        <h3>Correlation Rules</h3>
        {correlation?.rules?.map(rule => (
          <div key={rule.id} style={{ padding: '1rem', background: '#2a2a2a', marginBottom: '1rem', borderRadius: '8px' }}>
            <h4>{rule.name}</h4>
            <p>Triggered: {rule.triggered} times | Avg Score: {rule.avgScore}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default CorrelationAnalysis;
