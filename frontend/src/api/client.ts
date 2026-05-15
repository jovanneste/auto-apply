import axios from 'axios';
import type { Profile, QAPair, JobSummary, JobDetail, FormField } from '../types';

const api = axios.create({ baseURL: '/api' });

// Profile
export const getProfile = () => api.get<Profile>('/profile').then(r => r.data);
export const updateProfile = (data: Partial<Profile>) => api.put<Profile>('/profile', data).then(r => r.data);
export const uploadCV = (file: File) => {
  const form = new FormData();
  form.append('file', file);
  return api.post<Profile>('/profile/upload-cv', form).then(r => r.data);
};
export const getQAPairs = () => api.get<QAPair[]>('/profile/qa-pairs').then(r => r.data);
export const createQAPair = (data: { question: string; answer: string; tags?: string }) =>
  api.post<QAPair>('/profile/qa-pairs', data).then(r => r.data);
export const updateQAPair = (id: number, data: { question: string; answer: string; tags?: string }) =>
  api.put<QAPair>(`/profile/qa-pairs/${id}`, data).then(r => r.data);
export const deleteQAPair = (id: number) => api.delete(`/profile/qa-pairs/${id}`);

// Jobs
export const listJobs = () => api.get<JobSummary[]>('/jobs').then(r => r.data);
export const createJob = (url: string) => api.post<JobSummary>('/jobs', { url }).then(r => r.data);
export const getJob = (id: number) => api.get<JobDetail>(`/jobs/${id}`).then(r => r.data);
export const updateJob = (id: number, data: Partial<JobSummary>) =>
  api.put<JobSummary>(`/jobs/${id}`, data).then(r => r.data);
export const deleteJob = (id: number) => api.delete(`/jobs/${id}`);

// Analysis
export const startAnalysis = (jobId: number) => api.post(`/analysis/${jobId}/start`);
export const continueAnalysis = (jobId: number) => api.post(`/analysis/${jobId}/continue`);
export const updateField = (jobId: number, fieldId: number, finalAnswer: string) =>
  api.put<FormField>(`/analysis/${jobId}/fields/${fieldId}`, { final_answer: finalAnswer }).then(r => r.data);
