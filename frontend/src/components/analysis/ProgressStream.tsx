import { useEffect, useRef } from 'react';
import type { SSEEvent } from '../../types';
import { useSSE } from '../../hooks/useSSE';

interface Props {
  jobId: number;
  onComplete: (missingCount: number) => void;
  onNeedsAction: (action: string, message: string, jobId: number) => void;
  onError: (message: string) => void;
}

export default function ProgressStream({ jobId, onComplete, onNeedsAction, onError }: Props) {
  const logs = useRef<string[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);

  const streamUrl = `/api/analysis/${jobId}/stream`;

  useSSE(streamUrl, (event: SSEEvent) => {
    if (event.type === 'status' && event.message) {
      logs.current = [...logs.current, event.message];
      if (containerRef.current) {
        containerRef.current.innerHTML = logs.current
          .map(l => `<div class="text-sm text-slate-700">• ${l}</div>`)
          .join('');
        containerRef.current.scrollTop = containerRef.current.scrollHeight;
      }
    } else if (event.type === 'complete') {
      onComplete(event.missing_count ?? 0);
    } else if (event.type === 'needs_action' && event.action && event.message) {
      onNeedsAction(event.action, event.message, jobId);
    } else if (event.type === 'error' && event.message) {
      onError(event.message);
    }
  });

  return (
    <div className="mt-4 bg-slate-900 rounded-xl p-4 min-h-32 max-h-64 overflow-y-auto font-mono">
      <div className="text-xs text-emerald-400 mb-2 font-semibold">Analysis log</div>
      <div ref={containerRef} className="space-y-1" />
      <span className="inline-block w-2 h-4 bg-emerald-400 animate-pulse ml-1" />
    </div>
  );
}
