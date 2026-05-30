import { useCallback, useEffect, useRef, useState } from 'react';
import { getHealth } from '../api';
import { type HealthResponse } from '../types';

const POLL_MS = 30000;

interface HealthState {
  health: HealthResponse | null;
  offline: boolean;
  loading: boolean;
  lastChecked: number | null;
}

export function useHealth() {
  const [state, setState] = useState<HealthState>({
    health: null,
    offline: false,
    loading: true,
    lastChecked: null,
  });
  const mounted = useRef(true);

  const load = useCallback(async () => {
    const controller = new AbortController();
    try {
      const health = await getHealth(controller.signal);
      if (!mounted.current) return;
      setState({ health, offline: false, loading: false, lastChecked: Date.now() });
    } catch {
      if (!mounted.current) return;
      setState((s) => ({
        health: s.health,
        offline: true,
        loading: false,
        lastChecked: Date.now(),
      }));
    }
  }, []);

  useEffect(() => {
    mounted.current = true;
    void load();
    const id = window.setInterval(() => void load(), POLL_MS);
    return () => {
      mounted.current = false;
      window.clearInterval(id);
    };
  }, [load]);

  return state;
}
