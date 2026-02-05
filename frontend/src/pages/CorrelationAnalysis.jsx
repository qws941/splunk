import { useEffect, useState } from 'react';
import { Link2, GitBranch, TrendingUp, Clock } from 'lucide-react';
import './CorrelationAnalysis.css';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:3001';

function CorrelationAnalysis() {
  const [correlation, setCorrelation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('-24h');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/correlation?timeRange=${timeRange}`);
        const data = await res.json();
        setCorrelation(data);
      } catch (err) {
        console.error('Failed to fetch correlation:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [timeRange]);

  if (loading) {
    return <div className="loading">Loading correlation data...</div>;
  }

  const rules = correlation?.rules || [];
  const patterns = correlation?.patterns || [];

  return (
    <div className="correlation-page">
      <div className="page-header">
        <div>
          <h1>Correlation Analysis</h1>
          <p className="page-subtitle">Advanced event correlation and pattern detection</p>
        </div>
        <div className="time-selector">
          {['-1h', '-6h', '-24h', '-7d'].map(t => (
            <button
              key={t}
              className={`time-btn ${timeRange === t ? 'active' : ''}`}
              onClick={() => setTimeRange(t)}
            >
              {t.replace('-', '').toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      <div className="summary-cards">
        <div className="summary-card">
          <Link2 size={24} />
          <div>
            <span className="summary-value">{rules.length}</span>
            <span className="summary-label">Active Rules</span>
          </div>
        </div>
        <div className="summary-card">
          <GitBranch size={24} />
          <div>
            <span className="summary-value">{patterns.length}</span>
            <span className="summary-label">Patterns Detected</span>
          </div>
        </div>
        <div className="summary-card">
          <TrendingUp size={24} />
          <div>
            <span className="summary-value">
              {rules.reduce((sum, r) => sum + (r.triggered || 0), 0)}
            </span>
            <span className="summary-label">Total Triggers</span>
          </div>
        </div>
      </div>

      <section className="section">
        <h2>Correlation Rules</h2>
        <div className="rules-grid">
          {rules.length === 0 ? (
            <div className="no-data">No correlation rules configured</div>
          ) : (
            rules.map(rule => (
              <div key={rule.id} className="rule-card">
                <div className="rule-header">
                  <h3>{rule.name}</h3>
                  <span className={`rule-status ${rule.enabled ? 'enabled' : 'disabled'}`}>
                    {rule.enabled ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
                <div className="rule-stats">
                  <div className="rule-stat">
                    <span className="stat-num">{rule.triggered || 0}</span>
                    <span className="stat-text">Triggered</span>
                  </div>
                  <div className="rule-stat">
                    <span className="stat-num">{rule.avgScore || 0}</span>
                    <span className="stat-text">Avg Score</span>
                  </div>
                </div>
                {rule.lastTriggered && (
                  <div className="rule-footer">
                    <Clock size={14} />
                    <span>Last: {new Date(rule.lastTriggered).toLocaleString()}</span>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </section>

      {patterns.length > 0 && (
        <section className="section">
          <h2>Detected Patterns</h2>
          <div className="patterns-list">
            {patterns.map((pattern, idx) => (
              <div key={idx} className="pattern-item">
                <div className="pattern-info">
                  <span className="pattern-name">{pattern.name}</span>
                  <span className="pattern-type">{pattern.type}</span>
                </div>
                <div className="pattern-meta">
                  <span>{pattern.occurrences} occurrences</span>
                  <span>Confidence: {pattern.confidence}%</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

export default CorrelationAnalysis;
