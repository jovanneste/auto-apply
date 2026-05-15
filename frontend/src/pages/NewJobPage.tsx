import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createJob, startAnalysis, continueAnalysis } from '../api/client';
import ProgressStream from '../components/analysis/ProgressStream';

type Phase = 'idle' | 'analyzing' | 'needs_action' | 'done' | 'error';

export default function NewJobPage() {
  const [url, setUrl] = useState('');
  const [phase, setPhase] = useState<Phase>('idle');
  const [jobId, setJobId] = useState<number | null>(null);
  const [actionMessage, setActionMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    setPhase('analyzing');
    setErrorMessage('');

    const job = await createJob(url.trim());
    setJobId(job.id);
    await startAnalysis(job.id);
  };

  const handleComplete = (missingCount: number) => {
    setPhase('done');
    setTimeout(() => navigate(`/jobs/${jobId}`), 500);
  };

  const handleNeedsAction = (action: string, message: string, jid: number) => {
    setJobId(jid);
    setActionMessage(message);
    setPhase('needs_action');
  };

  const handleContinue = async () => {
    if (jobId) {
      await continueAnalysis(jobId);
      setPhase('analyzing');
    }
  };

  const handleError = (msg: string) => {
    setErrorMessage(msg);
    setPhase('error');
  };

  return (
    <div className="p-8 max-w-2xl">
      <h1 className="text-2xl font-bold text-slate-800 mb-2">New Application</h1>
      <p className="text-slate-500 text-sm mb-6">
        Paste the URL of the job application form (or the job posting page). The tool will find the form, fill it with your profile, and let you review everything.
      </p>

      <form onSubmit={handleSubmit} className="flex gap-2 mb-6">
        <input
          type="url"
          value={url}
          onChange={e => setUrl(e.target.value)}
          placeholder="https://boards.greenhouse.io/..."
          disabled={phase === 'analyzing'}
          className="flex-1 border border-slate-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={phase === 'analyzing' || !url.trim()}
          className="bg-emerald-600 text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-emerald-700 disabled:opacity-50"
        >
          {phase === 'analyzing' ? 'Analyzing...' : 'Analyze'}
        </button>
      </form>

      {phase === 'needs_action' && (
        <div className="mb-4 bg-yellow-50 border border-yellow-200 rounded-xl p-4">
          <p className="text-sm font-medium text-yellow-800 mb-3">⚠️ Action Required</p>
          <p className="text-sm text-yellow-700 mb-4">{actionMessage}</p>
          <button
            onClick={handleContinue}
            className="bg-yellow-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-yellow-700"
          >
            I'm done — Continue
          </button>
        </div>
      )}

      {phase === 'error' && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">
          <p className="font-medium mb-1">Analysis failed</p>
          <p>{errorMessage}</p>
          <button onClick={() => setPhase('idle')} className="mt-2 text-red-500 underline text-xs">
            Try again
          </button>
        </div>
      )}

      {phase === 'done' && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 text-sm text-emerald-700 font-medium">
          ✓ Analysis complete! Redirecting to review...
        </div>
      )}

      {jobId && (phase === 'analyzing' || phase === 'needs_action' || phase === 'done') && (
        <ProgressStream
          jobId={jobId}
          onComplete={handleComplete}
          onNeedsAction={handleNeedsAction}
          onError={handleError}
        />
      )}
    </div>
  );
}
