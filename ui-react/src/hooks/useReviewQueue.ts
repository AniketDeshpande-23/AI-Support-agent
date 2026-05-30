import { useState, useEffect, useCallback } from 'react';
import { getTickets } from '../api';
import { ApiError } from '../types';
import type { Ticket } from '../types';

export function useReviewQueue() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState<ApiError | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getTickets(100, 0, 'Human Review');
      setTickets(data);
    } catch (e) {
      setError(e instanceof ApiError ? e : new ApiError('server', 0, String(e)));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  return { tickets, loading, error, refresh: load };
}
