import { useEffect, useRef, useCallback } from 'react';
import { useStore } from '../store/store';

const MAX_RECONNECT_DELAY = 30000;
const INITIAL_RECONNECT_DELAY = 1000;

export const useWebSocket = () => {
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectDelayRef = useRef(INITIAL_RECONNECT_DELAY);
  const { setWsConnected, addRealtimeEvent, updateRealtimeStats } = useStore();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.hostname}:${import.meta.env.VITE_WS_PORT || 3001}/ws`;

    console.log('Connecting to WebSocket:', wsUrl);
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('✅ WebSocket connected');
      setWsConnected(true);
      reconnectDelayRef.current = INITIAL_RECONNECT_DELAY;

      // Subscribe to all channels
      ws.send(JSON.stringify({
        type: 'subscribe',
        channels: ['all', 'events', 'stats', 'alerts']
      }));
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);

        switch (message.type) {
          case 'connected':
            console.log('WebSocket client ID:', message.clientId);
            break;

          case 'events':
            if (message.data && Array.isArray(message.data)) {
              message.data.forEach(evt => addRealtimeEvent(evt));
            }
            break;

          case 'stats':
            if (message.data) {
              updateRealtimeStats(message.data);
            }
            break;

          case 'alert':
            console.log('🚨 Real-time alert:', message.data);
            break;

          case 'pong':
            // Heartbeat response
            break;

          default:
            console.log('Unknown message type:', message.type);
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      setWsConnected(false);
    };

    ws.onclose = () => {
      console.log('🔌 WebSocket disconnected');
      setWsConnected(false);

      // Exponential backoff reconnect
      const delay = reconnectDelayRef.current;
      reconnectTimeoutRef.current = setTimeout(() => {
        console.log(`Attempting to reconnect (delay: ${delay}ms)...`);
        connect();
      }, delay);
      reconnectDelayRef.current = Math.min(
        delay * 2,
        MAX_RECONNECT_DELAY
      );
    };

    wsRef.current = ws;
  }, [setWsConnected, addRealtimeEvent, updateRealtimeStats]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setWsConnected(false);
  }, [setWsConnected]);

  const send = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  useEffect(() => {
    // Send ping every 30 seconds to keep connection alive
    const pingInterval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        send({ type: 'ping' });
      }
    }, 30000);

    return () => {
      clearInterval(pingInterval);
    };
  }, [send]);

  return { connect, disconnect, send };
};
