import { create } from 'zustand';
import { api } from '../services/api';

export const useStore = create((set, get) => ({
  // State
  stats: null,
  events: [],
  alerts: [],
  correlation: null,
  threats: null,
  wsConnected: false,
  loading: false,
  error: null,

  // Actions
  setWsConnected: (connected) => set({ wsConnected: connected }),

  fetchStats: async () => {
    try {
      const stats = await api.getStats();
      set({ stats, error: null });
    } catch (error) {
      console.error('Failed to fetch stats:', error);
      set({ error: error.message });
    }
  },

  fetchEvents: async (params = {}) => {
    set({ loading: true });
    try {
      const data = await api.getEvents(params);
      set({ events: data.events, loading: false, error: null });
    } catch (error) {
      console.error('Failed to fetch events:', error);
      set({ loading: false, error: error.message });
    }
  },

  fetchAlerts: async () => {
    try {
      const data = await api.getAlerts();
      set({ alerts: data.alerts, error: null });
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
      set({ error: error.message });
    }
  },

  acknowledgeAlert: async (alertId, acknowledgedBy, comment) => {
    try {
      await api.acknowledgeAlert(alertId, acknowledgedBy, comment);
      // Refresh alerts
      await get().fetchAlerts();
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
      set({ error: error.message });
    }
  },

  fetchCorrelation: async (timeRange = '-24h') => {
    set({ loading: true });
    try {
      const data = await api.getCorrelation(timeRange);
      set({ correlation: data, loading: false, error: null });
    } catch (error) {
      console.error('Failed to fetch correlation:', error);
      set({ loading: false, error: error.message });
    }
  },

  fetchThreats: async () => {
    try {
      const data = await api.getThreats();
      set({ threats: data, error: null });
    } catch (error) {
      console.error('Failed to fetch threats:', error);
      set({ error: error.message });
    }
  },

  addRealtimeEvent: (event) => {
    set((state) => ({
      events: [event, ...state.events].slice(0, 100) // Keep last 100 events
    }));
  },

  updateRealtimeStats: (stats) => {
    set({ stats });
  },

  clearError: () => set({ error: null })
}));
