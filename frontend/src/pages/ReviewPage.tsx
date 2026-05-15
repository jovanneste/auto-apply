import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getJob } from '../api/client';
import { useJobStore } from '../store/jobStore';
import FieldTable from '../components/review/FieldTable';
import InstructionsPanel from '../components/instructions/InstructionsPanel';

export default function ReviewPage() {
  const { id } = useParams<{ id: string }>();
  const jobId = Number(id);
  const { currentJob, setCurrentJob } = useJobStore();
  const [loading, setLoading] = useState(true);
  const [showInstructions, setShowInstructions] = useState(false);

  useEffect(() => {
    getJob(jobId).then(job => {
      setCurrentJob(job);
      setLoading(false);
    });
  }, [jobId]);

  if (loading || !currentJob) {
    return <div className="p-8 text-slate-500">Loading application...</div>;
  }

  const missingRequired = currentJob.fields.filter(
    f => f.is_required && f.confidence === 'missing' && !f.final_answer
  ).length;

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Left panel: job info */}
      <div className="w-80 shrink-0 border-r border-slate-200 bg-white overflow-y-auto flex flex-col">
        <div className="p-5 border-b border-slate-200">
          <h2 className="font-bold text-slate-800 text-lg leading-tight">
            {currentJob.title || 'Untitled Position'}
          </h2>
          <p className="text-sm text-slate-500 mt-1">{currentJob.organization}</p>
          <a href={currentJob.url} target="_blank" rel="noopener noreferrer"
            className="text-xs text-emerald-600 hover:underline mt-1 block truncate">
            {currentJob.url}
          </a>
          <div className="flex gap-2 mt-3">
            <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
              {currentJob.ats_type || 'generic'}
            </span>
            <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
              {currentJob.fields.length} fields
            </span>
          </div>
        </div>

        {currentJob.screenshot_path && (
          <div className="p-4">
            <p className="text-xs text-slate-400 mb-2 font-medium uppercase tracking-wide">Page screenshot</p>
            <img
              src={`/screenshots/job_screenshot.png`}
              alt="Application page"
              className="w-full rounded border border-slate-200 shadow-sm"
            />
          </div>
        )}
      </div>

      {/* Right panel: field table */}
      <div className="flex-1 overflow-y-auto bg-white pb-24">
        <div className="px-6 py-5 border-b border-slate-200">
          <h2 className="font-semibold text-slate-800">Review & Edit Answers</h2>
          <p className="text-sm text-slate-500 mt-0.5">
            All fields Claude filled from your profile. Edit any answer before generating instructions.
          </p>
        </div>
        <div className="px-2">
          <FieldTable fields={currentJob.fields} jobId={jobId} />
        </div>
      </div>

      {/* Sticky bottom bar */}
      <div className="fixed bottom-0 right-0 left-56 bg-white border-t border-slate-200 px-8 py-4 flex items-center justify-between">
        {missingRequired > 0 ? (
          <p className="text-sm text-red-600">
            ⚠️ {missingRequired} required field{missingRequired !== 1 ? 's' : ''} still need{missingRequired === 1 ? 's' : ''} input
          </p>
        ) : (
          <p className="text-sm text-emerald-600">✓ All required fields filled</p>
        )}
        <button
          onClick={() => setShowInstructions(true)}
          disabled={missingRequired > 0}
          className="bg-emerald-600 text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-emerald-700 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Generate Instructions →
        </button>
      </div>

      {showInstructions && (
        <InstructionsPanel jobId={jobId} onClose={() => setShowInstructions(false)} />
      )}
    </div>
  );
}
