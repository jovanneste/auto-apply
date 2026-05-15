import { useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { useJobStore } from '../../store/jobStore';

interface Props {
  jobId: number;
  onClose: () => void;
}

export default function InstructionsPanel({ jobId, onClose }: Props) {
  const { instructions, appendInstructions, clearInstructions } = useJobStore();
  const fetchedRef = useRef(false);

  useEffect(() => {
    if (fetchedRef.current) return;
    fetchedRef.current = true;
    clearInstructions();

    const es = new EventSource(`/api/instructions/${jobId}/generate`);
    es.onmessage = (e) => {
      appendInstructions(e.data);
    };
    es.onerror = () => es.close();
    return () => es.close();
  }, [jobId]);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(instructions);
  };

  const print = () => window.print();

  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="flex-1 bg-black/40" onClick={onClose} />
      <div className="w-full max-w-2xl bg-white h-full shadow-2xl flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <h2 className="text-lg font-semibold text-slate-800">Submission Instructions</h2>
          <div className="flex gap-2">
            <button onClick={copyToClipboard}
              className="text-sm bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded-lg">
              Copy text
            </button>
            <button onClick={print}
              className="text-sm bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded-lg">
              Print
            </button>
            <button onClick={onClose}
              className="text-sm text-slate-400 hover:text-slate-700 px-2">✕</button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4 prose prose-sm max-w-none">
          {instructions ? (
            <ReactMarkdown>{instructions}</ReactMarkdown>
          ) : (
            <div className="flex items-center gap-2 text-slate-500">
              <span className="animate-spin">⟳</span>
              Generating instructions...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
