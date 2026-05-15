import { useEffect, useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { getProfile, updateProfile, uploadCV, getQAPairs, createQAPair, updateQAPair, deleteQAPair } from '../api/client';
import type { Profile, QAPair } from '../types';

// Sections for the profile accordion
const JSON_FIELDS: { key: keyof Profile; label: string }[] = [
  { key: 'education_json', label: 'Education' },
  { key: 'work_history_json', label: 'Work History' },
  { key: 'publications_json', label: 'Publications' },
  { key: 'fieldwork_json', label: 'Fieldwork' },
  { key: 'grants_json', label: 'Grants' },
  { key: 'awards_json', label: 'Awards' },
  { key: 'skills_json', label: 'Skills' },
];

const TEXT_FIELDS: { key: keyof Profile; label: string; rows?: number }[] = [
  { key: 'full_name', label: 'Full Name' },
  { key: 'email', label: 'Email' },
  { key: 'phone', label: 'Phone' },
  { key: 'address', label: 'Address' },
  { key: 'linkedin', label: 'LinkedIn URL' },
  { key: 'website', label: 'Website' },
  { key: 'summary', label: 'Professional Summary', rows: 4 },
  { key: 'species_expertise', label: 'Species Expertise (comma-separated)' },
  { key: 'field_sites', label: 'Field Sites / Regions' },
  { key: 'conservation_philosophy', label: 'Conservation Philosophy', rows: 3 },
  { key: 'teaching_experience', label: 'Teaching Experience', rows: 3 },
];

export default function ProfilePage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [qaPairs, setQAPairs] = useState<QAPair[]>([]);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [saved, setSaved] = useState(false);
  const [newQ, setNewQ] = useState('');
  const [newA, setNewA] = useState('');
  const [openSection, setOpenSection] = useState<string | null>('basic');

  useEffect(() => {
    getProfile().then(setProfile);
    getQAPairs().then(setQAPairs);
  }, []);

  const onDrop = useCallback(async (files: File[]) => {
    if (!files[0]) return;
    setUploading(true);
    const updated = await uploadCV(files[0]);
    setProfile(updated);
    setUploading(false);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    multiple: false,
  });

  const handleSave = async () => {
    if (!profile) return;
    setSaving(true);
    const updated = await updateProfile(profile);
    setProfile(updated);
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleField = (key: keyof Profile, value: string) => {
    setProfile(p => p ? { ...p, [key]: value } : p);
  };

  const addQAPair = async () => {
    if (!newQ.trim() || !newA.trim()) return;
    const pair = await createQAPair({ question: newQ, answer: newA });
    setQAPairs(prev => [...prev, pair]);
    setNewQ('');
    setNewA('');
  };

  const removeQAPair = async (id: number) => {
    await deleteQAPair(id);
    setQAPairs(prev => prev.filter(p => p.id !== id));
  };

  if (!profile) return <div className="p-8 text-slate-500">Loading profile...</div>;

  const Section = ({ id, title, children }: { id: string; title: string; children: React.ReactNode }) => (
    <div className="border border-slate-200 rounded-xl overflow-hidden mb-3">
      <button
        onClick={() => setOpenSection(openSection === id ? null : id)}
        className="w-full flex items-center justify-between px-5 py-4 bg-white hover:bg-slate-50 text-left"
      >
        <span className="font-medium text-slate-800">{title}</span>
        <span className="text-slate-400 text-sm">{openSection === id ? '▲' : '▼'}</span>
      </button>
      {openSection === id && <div className="px-5 py-4 border-t border-slate-100 bg-white">{children}</div>}
    </div>
  );

  return (
    <div className="p-8 max-w-3xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">My Profile</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Claude uses this data to fill application forms automatically.
          </p>
        </div>
        <button
          onClick={handleSave}
          disabled={saving}
          className="bg-emerald-600 text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-emerald-700 disabled:opacity-50"
        >
          {saved ? '✓ Saved!' : saving ? 'Saving...' : 'Save Profile'}
        </button>
      </div>

      {/* CV Upload */}
      <Section id="cv" title="CV / Resume Upload">
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
            isDragActive ? 'border-emerald-400 bg-emerald-50' : 'border-slate-300 hover:border-slate-400'
          }`}
        >
          <input {...getInputProps()} />
          {uploading ? (
            <p className="text-slate-500">Uploading and parsing CV with Claude...</p>
          ) : profile.cv_file_path ? (
            <div>
              <p className="text-emerald-700 font-medium">✓ CV uploaded and parsed</p>
              <p className="text-xs text-slate-400 mt-1">{profile.cv_file_path.split('/').pop()}</p>
              <p className="text-xs text-slate-500 mt-2">Drop a new PDF to replace it</p>
            </div>
          ) : (
            <div>
              <p className="text-4xl mb-2">📄</p>
              <p className="text-slate-600 font-medium">Drop your CV here, or click to browse</p>
              <p className="text-xs text-slate-400 mt-1">PDF only</p>
            </div>
          )}
        </div>
      </Section>

      {/* Basic Info */}
      <Section id="basic" title="Basic Information">
        <div className="grid grid-cols-2 gap-4">
          {TEXT_FIELDS.slice(0, 6).map(({ key, label }) => (
            <div key={key}>
              <label className="text-xs font-medium text-slate-600 block mb-1">{label}</label>
              <input
                type="text"
                value={(profile[key] as string) || ''}
                onChange={e => handleField(key, e.target.value)}
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
          ))}
        </div>
      </Section>

      {/* Wildlife-specific text fields */}
      <Section id="bio" title="Professional Background">
        <div className="space-y-4">
          {TEXT_FIELDS.slice(6).map(({ key, label, rows }) => (
            <div key={key}>
              <label className="text-xs font-medium text-slate-600 block mb-1">{label}</label>
              <textarea
                value={(profile[key] as string) || ''}
                onChange={e => handleField(key, e.target.value)}
                rows={rows || 2}
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 resize-y"
              />
            </div>
          ))}
        </div>
      </Section>

      {/* JSON sections — shown as editable raw JSON for now */}
      {JSON_FIELDS.map(({ key, label }) => (
        <Section key={key} id={key} title={label}>
          <p className="text-xs text-slate-400 mb-2">
            Raw JSON — auto-populated from CV upload. Edit carefully or re-upload CV.
          </p>
          <textarea
            value={(profile[key] as string) || '[]'}
            onChange={e => handleField(key, e.target.value)}
            rows={6}
            className="w-full border border-slate-300 rounded-lg px-3 py-2 text-xs font-mono focus:outline-none focus:ring-2 focus:ring-emerald-500 resize-y"
          />
        </Section>
      ))}

      {/* Q&A Pairs */}
      <Section id="qa" title="Common Q&A Pairs">
        <p className="text-xs text-slate-500 mb-4">
          Add stock answers to common application questions. Claude will use these when matching form fields.
        </p>
        <div className="space-y-3 mb-4">
          {qaPairs.map(pair => (
            <div key={pair.id} className="bg-slate-50 rounded-lg p-3 flex items-start justify-between gap-3">
              <div>
                <p className="text-xs font-medium text-slate-700">{pair.question}</p>
                <p className="text-sm text-slate-600 mt-1 whitespace-pre-wrap">{pair.answer}</p>
              </div>
              <button onClick={() => removeQAPair(pair.id)}
                className="text-xs text-red-400 hover:text-red-600 shrink-0">✕</button>
            </div>
          ))}
        </div>
        <div className="border border-slate-200 rounded-lg p-4 bg-slate-50 space-y-3">
          <p className="text-xs font-medium text-slate-600">Add new Q&A pair</p>
          <input
            type="text"
            placeholder="Question (e.g. Why do you want to work in conservation?)"
            value={newQ}
            onChange={e => setNewQ(e.target.value)}
            className="w-full border border-slate-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
          <textarea
            placeholder="Your answer..."
            value={newA}
            onChange={e => setNewA(e.target.value)}
            rows={3}
            className="w-full border border-slate-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 resize-y"
          />
          <button onClick={addQAPair}
            disabled={!newQ.trim() || !newA.trim()}
            className="bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-emerald-700 disabled:opacity-50">
            Add pair
          </button>
        </div>
      </Section>
    </div>
  );
}
