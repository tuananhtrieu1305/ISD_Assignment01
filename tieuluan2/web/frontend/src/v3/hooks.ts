import { useEffect, useState } from "react";
export function useResource<T>(
  key: string,
  load: (signal: AbortSignal) => Promise<T>,
) {
  const [state, set] = useState<{
    key: string;
    value: T | null;
    error: Error | null;
    loading: boolean;
  }>({ key, value: null, error: null, loading: true });
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    set({ key, value: null, error: null, loading: true });
    load(controller.signal)
      .then((value) => {
        if (active) set({ key, value, error: null, loading: false });
      })
      .catch((error) => {
        if (active && error.name !== "AbortError")
          set({ key, value: null, error, loading: false });
      });
    return () => {
      active = false;
      controller.abort();
    };
    // key is the full request identity. Load captures only values included in key.
  }, [key, retry]);
  return {
    ...(state.key === key
      ? state
      : { value: null, error: null, loading: true }),
    retry: () => setRetry((n) => n + 1),
  };
}
