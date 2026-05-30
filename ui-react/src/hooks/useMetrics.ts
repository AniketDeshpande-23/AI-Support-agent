import { useCallback, useEffect, useRef, useState } from 'react';
import { getMetrics, getTickets } from '../api';
import { ApiError, type Metrics, type Ticket } from '../types';

export interface MetricsBundle {
  metrics: Metrics;
  tickets: Ticket[];
}

interface MetricsState {
  data: MetricsBundle | null;
  loading: boolean;
  error: ApiError | null;
}

export function useMetrics(autoRefreshMs: number | null) {
  const [state, setState] = useState<MetricsState>({
    data: null,
    loading: true,
    error: null,
  });
  const mounted = useRef(true);

  const load = useCallback(async (silent: boolean) => {
    if (!silent) setState((s) => ({ ...s, loading: true, error: null }));
    const controller = new AbortController();
    try {
      const [metrics, tickets] = await Promise.all([
        getMetrics(controller.signal),
        getTickets(200, 0, undefined, controller.signal),
      ]);
      if (!mounted.current) return;
      setState({ data: { metrics, tickets }, loading: false, error: null });
    } catch (err) {
      if (!mounted.current) return;
      const apiErr =
        err instanceof ApiError ? err : new ApiError('server', 500, 'Unexpected error');
      setState((s) => ({ data: s.data, loading: false, error: apiErr }));
    }
  }, []);

  useEffect(() => {
    mounted.current = true;
    void load(false);
    return () => {
      mounted.current = false;
    };
  }, [load]);

  useEffect(() => {
    if (autoRefreshMs === null) return;
    const id = window.setInterval(() => void load(true), autoRefreshMs);
    return () => window.clearInterval(id);
  }, [autoRefreshMs, load]);

  return { ...state, refresh: () => load(false) };
}
