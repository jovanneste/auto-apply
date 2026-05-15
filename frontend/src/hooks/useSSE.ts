import { useEffect, useRef } from 'react';
import type { SSEEvent } from '../types';

export function useSSE(url: string | null, onEvent: (event: SSEEvent) => void) {
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  useEffect(() => {
    if (!url) return;
    const es = new EventSource(url);

    es.onmessage = (e) => {
      try {
        const data: SSEEvent = JSON.parse(e.data);
        onEventRef.current(data);
        if (data.type === 'complete' || data.type === 'error') {
          es.close();
        }
      } catch {
        // ignore parse errors for ping events
      }
    };

    es.onerror = () => {
      es.close();
    };

    return () => es.close();
  }, [url]);
}
