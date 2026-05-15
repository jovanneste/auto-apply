import { create } from 'zustand';
import type { JobDetail, FormField } from '../types';

interface JobStore {
  currentJob: JobDetail | null;
  setCurrentJob: (job: JobDetail | null) => void;
  updateFieldAnswer: (fieldId: number, answer: string) => void;
  instructions: string;
  appendInstructions: (chunk: string) => void;
  clearInstructions: () => void;
}

export const useJobStore = create<JobStore>((set) => ({
  currentJob: null,
  setCurrentJob: (job) => set({ currentJob: job }),
  updateFieldAnswer: (fieldId, answer) =>
    set((state) => {
      if (!state.currentJob) return state;
      return {
        currentJob: {
          ...state.currentJob,
          fields: state.currentJob.fields.map((f) =>
            f.id === fieldId ? { ...f, final_answer: answer, user_edited: true } : f
          ),
        },
      };
    }),
  instructions: '',
  appendInstructions: (chunk) => set((state) => ({ instructions: state.instructions + chunk })),
  clearInstructions: () => set({ instructions: '' }),
}));
