/**
 * API Client for Backend REST API
 */

const API_BASE = import.meta.env.VITE_API_URL || '/api';

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;

  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || `HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API request failed: ${url}`, error);
    throw error;
  }
}

export const api = {
  // Events
  getEvents: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return request(`/events${query ? '?' + query : ''}`);
  },

  // Statistics
  getStats: () => request('/stats'),

  // Correlation
  getCorrelation: (timeRange = '-24h') => {
    return request(`/correlation?timeRange=${encodeURIComponent(timeRange)}`);
  },

  // Alerts
  getAlerts: () => request('/alerts'),

  acknowledgeAlert: (alertId, acknowledgedBy, comment) => {
    return request('/alerts/acknowledge', {
      method: 'POST',
      body: JSON.stringify({ alertId, acknowledgedBy, comment })
    });
  },

  // Threats
  getThreats: () => request('/threats'),

  // Dashboards
  getDashboards: () => request('/dashboards'),

  // Slack test
  testSlack: () => request('/slack/test')
};
