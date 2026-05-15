import { useState } from 'react';
import type { FormField } from '../../types';
import { updateField } from '../../api/client';
import { useJobStore } from '../../store/jobStore';

const CONFIDENCE_STYLES: Record<string, string> = {
  high: 'bg-emerald-100 text-emerald-700',
  medium: 'bg-yellow-100 text-yellow-700',
  low: 'bg-orange-100 text-orange-700',
  missing: 'bg-red-100 text-red-700',
};

const SOURCE_LABELS: Record<string, string> = {
  profile: 'From CV',
  qa_pair: 'From Q&A',
  inferred: 'Inferred',
  missing: 'Needs input',
};

interface FieldRowProps {
  field: FormField;
  jobId: number;
}

function FieldRow({ field, jobId }: FieldRowProps) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(field.final_answer ?? field.proposed_answer ?? '');
  const [saving, setSaving] = useState(false);
  const updateFieldAnswer = useJobStore(s => s.updateFieldAnswer);

  const isMissing = field.confidence === 'missing' && !field.final_answer;
  const options = field.options_json ? JSON.parse(field.options_json) : null;

  const save = async () => {
    setSaving(true);
    await updateField(jobId, field.id, draft);
    updateFieldAnswer(field.id, draft);
    setSaving(false);
    setEditing(false);
  };

  const displayAnswer = field.final_answer ?? field.proposed_answer ?? '';

  return (
    <tr className={`border-b border-slate-100 ${isMissing ? 'bg-red-50 border-l-4 border-l-red-400' : ''}`}>
      <td className="px-4 py-3 align-top">
        <div className="flex items-start gap-1">
          <span className="text-sm font-medium text-slate-800">
            {field.field_label || field.field_name || '—'}
          </span>
          {field.is_required && <span className="text-red-500 text-xs mt-0.5">*</span>}
        </div>
        <div className="flex gap-1 mt-1 flex-wrap">
          <span className="text-xs bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded">
            {field.field_type}
          </span>
          <span className="text-xs bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded">
            p{field.page_number}
          </span>
        </div>
      </td>

      <td className="px-4 py-3 align-top">
        {editing ? (
          <div className="flex flex-col gap-2">
            {options ? (
              <select
                value={draft}
                onChange={e => setDraft(e.target.value)}
                className="w-full border border-slate-300 rounded px-2 py-1 text-sm"
              >
                <option value="">— select —</option>
                {options.map((o: { value: string; label: string }) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            ) : field.field_type === 'textarea' ? (
              <textarea
                value={draft}
                onChange={e => setDraft(e.target.value)}
                rows={6}
                className="w-full border border-slate-300 rounded px-2 py-1 text-sm font-mono resize-y"
              />
            ) : (
              <input
                type="text"
                value={draft}
                onChange={e => setDraft(e.target.value)}
                className="w-full border border-slate-300 rounded px-2 py-1 text-sm"
              />
            )}
            <div className="flex gap-2">
              <button onClick={save} disabled={saving}
                className="text-xs bg-emerald-600 text-white px-3 py-1 rounded hover:bg-emerald-700 disabled:opacity-50">
                {saving ? 'Saving...' : 'Save'}
              </button>
              <button onClick={() => setEditing(false)}
                className="text-xs text-slate-500 px-3 py-1 rounded hover:bg-slate-100">
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="flex items-start justify-between gap-2">
            <span className={`text-sm whitespace-pre-wrap break-words max-w-xs ${!displayAnswer ? 'text-red-500 italic' : 'text-slate-700'}`}>
              {displayAnswer || 'No answer — click to fill'}
            </span>
            <button onClick={() => setEditing(true)}
              className="text-xs text-slate-400 hover:text-slate-700 shrink-0">✎</button>
          </div>
        )}
        {field.reasoning && !editing && (
          <p className="text-xs text-slate-400 mt-1 italic">{field.reasoning}</p>
        )}
      </td>

      <td className="px-4 py-3 align-top whitespace-nowrap">
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${CONFIDENCE_STYLES[field.confidence ?? 'missing']}`}>
          {field.confidence ?? 'missing'}
        </span>
        <div className="text-xs text-slate-400 mt-1">
          {SOURCE_LABELS[field.source ?? 'missing']}
        </div>
      </td>
    </tr>
  );
}

interface Props {
  fields: FormField[];
  jobId: number;
}

export default function FieldTable({ fields, jobId }: Props) {
  const sorted = [...fields].sort((a, b) => {
    const aMissing = !a.final_answer && a.confidence === 'missing' ? 0 : 1;
    const bMissing = !b.final_answer && b.confidence === 'missing' ? 0 : 1;
    if (aMissing !== bMissing) return aMissing - bMissing;
    return (a.page_number - b.page_number) || ((a.display_order ?? 0) - (b.display_order ?? 0));
  });

  const missingCount = fields.filter(f => f.confidence === 'missing' && !f.final_answer).length;

  return (
    <div>
      {missingCount > 0 && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700 font-medium sticky top-0">
          ⚠️ {missingCount} field{missingCount !== 1 ? 's' : ''} need{missingCount === 1 ? 's' : ''} your input
        </div>
      )}
      <table className="w-full text-left">
        <thead>
          <tr className="border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wide">
            <th className="px-4 py-2">Field</th>
            <th className="px-4 py-2">Answer</th>
            <th className="px-4 py-2">Confidence</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map(f => (
            <FieldRow key={f.id} field={f} jobId={jobId} />
          ))}
        </tbody>
      </table>
    </div>
  );
}
