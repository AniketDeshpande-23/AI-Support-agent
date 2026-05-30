import { useCallback, useRef, useState } from 'react';
import { analyze } from '../api';
import { ApiError, type AnalyzeResult } from '../types';

interface AnalyzeState {
  result: AnalyzeResult | null;
  loading: boolean;
  error: ApiError | null;
}

export function useAnalyze() {
  const [state, setState] = useState<AnalyzeState>({
    result: null,
    loading: false,
    error: null,
  });
  const abortRef = useRef<AbortController | null>(null);

  const run = useCallback(async (text: string) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const result = await analyze(text, controller.signal);
      if (controller.signal.aborted) return;
      setState({ result, loading: false, error: null });
    } catch (err) {
      if (controller.signal.aborted) return;
      const apiErr =
        err instanceof ApiError ? err : new ApiError('server', 500, 'Unexpected error');
      setState((s) => ({ ...s, loading: false, error: apiErr }));
    }
  }, []);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setState({ result: null, loading: false, error: null });
  }, []);

  return { ...state, run, reset };
}
