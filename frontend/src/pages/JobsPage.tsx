import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { listJobs, deleteJob } from '../api/client';
import type { JobSummary, JobStatus } from '../types';

const STATUS_STYLES: Record<JobStatus, string> = {
  pending: 'bg-slate-100 text-slate-600',
  analyzing: 'bg-blue-100 text-blue-700 animate-pulse',
  needs_input: 'bg-yellow-100 text-yellow-700',
  ready: 'bg-emerald-100 text-emerald-700',
  complete: 'bg-slate-100 text-slate-500',
};

export default function JobsPage() {
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listJobs().then(setJobs).finally(() => setLoading(false));
  }, []);

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this application?')) return;
    await deleteJob(id);
    setJobs(prev => prev.filter(j => j.id !== id));
  };

  if (loading) return <div className="p-8 text-slate-500">Loading applications...</div>;

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Applications</h1>
        <Link to="/new"
          className="bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-emerald-700">
          + New Application
        </Link>
      </div>

      {jobs.length === 0 ? (
        <div className="text-center py-20 text-slate-400">
          <p className="text-5xl mb-4">📋</p>
          <p className="text-lg font-medium">No applications yet</p>
          <p className="text-sm mt-2">Paste a job URL to get started</p>
          <Link to="/new" className="mt-4 inline-block bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-emerald-700">
            Start first application
          </Link>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wide bg-slate-50">
                <th className="px-4 py-3">Position</th>
                <th className="px-4 py-3">ATS</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Date</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {jobs.map(job => (
                <tr key={job.id} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <Link to={`/jobs/${job.id}`} className="font-medium text-slate-800 hover:text-emerald-700">
                      {job.title || 'Untitled Position'}
                    </Link>
                    <div className="text-xs text-slate-500">{job.organization || new URL(job.url).hostname}</div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
                      {job.ats_type || 'unknown'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_STYLES[job.status]}`}>
                      {job.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-500">
                    {new Date(job.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link to={`/jobs/${job.id}`}
                      className="text-xs text-emerald-600 hover:text-emerald-700 mr-3">
                      Open
                    </Link>
                    <button onClick={() => handleDelete(job.id)}
                      className="text-xs text-red-400 hover:text-red-600">
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
