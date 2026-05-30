import { useCallback, useEffect, useRef, useState } from 'react';
import { getTickets } from '../api';
import { ApiError, type Ticket } from '../types';

const POLL_MS = 5000;

interface FeedState {
  tickets: Ticket[];
  loading: boolean;
  error: ApiError | null;
  lastUpdated: number | null;
}

export function useLiveFeed(paused: boolean) {
  const [state, setState] = useState<FeedState>({
    tickets: [],
    loading: true,
    error: null,
    lastUpdated: null,
  });
  const mounted = useRef(true);
  const inFlight = useRef(false);

  const load = useCallback(async (silent: boolean) => {
    if (inFlight.current) return;
    inFlight.current = true;
    if (!silent) setState((s) => ({ ...s, loading: true, error: null }));
    const controller = new AbortController();
    try {
      const tickets = await getTickets(25, 0, controller.signal);
      if (!mounted.current) return;
      setState({ tickets, loading: false, error: null, lastUpdated: Date.now() });
    } catch (err) {
      if (!mounted.current) return;
      const apiErr =
        err instanceof ApiError ? err : new ApiError('server', 500, 'Unexpected error');
      setState((s) => ({ ...s, loading: false, error: apiErr }));
    } finally {
      inFlight.current = false;
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
    if (paused) return;
    const id = window.setInterval(() => void load(true), POLL_MS);
    return () => window.clearInterval(id);
  }, [paused, load]);

  return { ...state, refresh: () => load(false) };
}
