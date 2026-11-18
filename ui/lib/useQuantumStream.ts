'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { SimulationRequest, QuantumEvent } from './types';
import { useQuantumStore } from './quantumStore';

interface UseQuantumStreamOptions {
  url?: string;
  autoConnect?: boolean;
}

interface UseQuantumStreamReturn {
  isConnected: boolean;
  error: string | null;
  send: (request: SimulationRequest) => void;
}

const DEFAULT_WS_URL = 'ws://localhost:8000/ws/simulate';
const MAX_RECONNECT_ATTEMPTS = 5;

export function useQuantumStream(
  initialRequest?: SimulationRequest,
  options?: UseQuantumStreamOptions
): UseQuantumStreamReturn {
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef<number>(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const eventBufferRef = useRef<QuantumEvent[]>([]);
  const rafIdRef = useRef<number | null>(null);
  const pendingRequestRef = useRef<SimulationRequest | undefined>(initialRequest);
  const isUnmountedRef = useRef<boolean>(false);

  const targetUrl = options?.url || DEFAULT_WS_URL;

  // Flush buffered events at ~60fps via requestAnimationFrame
  const scheduleFlush = useCallback(() => {
    if (rafIdRef.current !== null) return;

    rafIdRef.current = requestAnimationFrame(() => {
      rafIdRef.current = null;
      if (eventBufferRef.current.length === 0) return;

      const eventsToFlush = [...eventBufferRef.current];
      eventBufferRef.current = [];

      const { handleEvent } = useQuantumStore.getState();
      for (const ev of eventsToFlush) {
        handleEvent(ev);
      }
    });
  }, []);

  const connect = useCallback(() => {
    if (isUnmountedRef.current) return;
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    try {
      const ws = new WebSocket(targetUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        if (isUnmountedRef.current) {
          ws.close();
          return;
        }
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;

        // Send initial or pending simulation request if available
        if (pendingRequestRef.current) {
          useQuantumStore.getState().startSimulation();
          ws.send(JSON.stringify(pendingRequestRef.current));
          pendingRequestRef.current = undefined;
        }
      };

      ws.onmessage = (messageEvent) => {
        try {
          const parsed = JSON.parse(messageEvent.data);
          if (parsed && typeof parsed === 'object' && 'event_type' in parsed) {
            eventBufferRef.current.push(parsed as QuantumEvent);
            scheduleFlush();
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.onerror = () => {
        setError('WebSocket error encountered');
      };

      ws.onclose = () => {
        setIsConnected(false);
        wsRef.current = null;

        if (isUnmountedRef.current) return;

        if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 16000);
          reconnectAttemptsRef.current += 1;
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        } else {
          setError(`WebSocket connection closed. Reconnect limit (${MAX_RECONNECT_ATTEMPTS}) reached.`);
        }
      };
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create WebSocket connection');
    }
  }, [targetUrl, scheduleFlush]);

  const send = useCallback(
    (request: SimulationRequest) => {
      useQuantumStore.getState().startSimulation();

      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify(request));
      } else {
        pendingRequestRef.current = request;
        connect();
      }
    },
    [connect]
  );

  useEffect(() => {
    isUnmountedRef.current = false;
    connect();

    return () => {
      isUnmountedRef.current = true;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (rafIdRef.current !== null) {
        cancelAnimationFrame(rafIdRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect]);

  return { isConnected, error, send };
}
