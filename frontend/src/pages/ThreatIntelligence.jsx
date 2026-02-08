import { useEffect, useState } from 'react';
import { Target, Globe, AlertTriangle, TrendingUp } from 'lucide-react';
import './ThreatIntelligence.css';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:3001';

function ThreatIntelligence() {
  const [threats, setThreats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/threats`);
        const data = await res.json();
        setThreats(data);
      } catch (err) {
        console.error('Failed to fetch threats:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div className="loading">Loading threat intelligence...</div>;
  }

  const topThreats = threats?.topThreats || [];
  const geoData = threats?.geoDistribution || [];
  const summary = threats?.summary || {};

  return (
    <div className="threat-page">
      <div className="page-header">
        <h1>Threat Intelligence</h1>
        <p className="page-subtitle">Threat analysis and geolocation insights</p>
      </div>

      <div className="summary-cards">
        <div className="summary-card danger">
          <AlertTriangle size={24} />
          <div>
            <span className="summary-value">{summary.criticalThreats || 0}</span>
            <span className="summary-label">Critical Threats</span>
          </div>
        </div>
        <div className="summary-card">
          <Target size={24} />
          <div>
            <span className="summary-value">{summary.activeThreats || topThreats.length}</span>
            <span className="summary-label">Active Sources</span>
          </div>
        </div>
        <div className="summary-card">
          <Globe size={24} />
          <div>
            <span className="summary-value">{summary.countries || geoData.length}</span>
            <span className="summary-label">Countries</span>
          </div>
        </div>
        <div className="summary-card">
          <TrendingUp size={24} />
          <div>
            <span className="summary-value">{summary.blockedToday || 0}</span>
            <span className="summary-label">Blocked Today</span>
          </div>
        </div>
      </div>

      <section className="section">
        <h2>Top Threat Sources</h2>
        <div className="threats-table">
          <table>
            <thead>
              <tr>
                <th>IP Address</th>
                <th>Country</th>
                <th>Abuse Score</th>
                <th>Events</th>
                <th>Category</th>
              </tr>
            </thead>
            <tbody>
              {topThreats.length === 0 ? (
                <tr><td colSpan={5} className="no-data">No threats detected</td></tr>
              ) : (
                topThreats.map((threat, idx) => (
                  <tr key={idx}>
                    <td className="ip-cell">
                      <code>{threat.ip}</code>
                    </td>
                    <td>
                      <span className="country-badge">{threat.country}</span>
                    </td>
                    <td>
                      <span className={`abuse-score score-${getScoreLevel(threat.abuseScore)}`}>
                        {threat.abuseScore}%
                      </span>
                    </td>
                    <td>{threat.eventCount}</td>
                    <td>{threat.category || 'Unknown'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      {geoData.length > 0 && (
        <section className="section">
          <h2>Geographic Distribution</h2>
          <div className="geo-list">
            {geoData.map((geo, idx) => (
              <div key={idx} className="geo-item">
                <div className="geo-info">
                  <span className="geo-country">{geo.country}</span>
                  <span className="geo-count">{geo.count} events</span>
                </div>
                <div className="geo-bar">
                  <div
                    className="geo-fill"
                    style={{ width: `${Math.min(100, (geo.count / (geoData[0]?.count || 1)) * 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

function getScoreLevel(score) {
  if (score >= 80) return 'critical';
  if (score >= 50) return 'high';
  if (score >= 30) return 'medium';
  return 'low';
}

export default ThreatIntelligence;
