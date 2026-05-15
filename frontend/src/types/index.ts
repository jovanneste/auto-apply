export interface Profile {
  id: number;
  full_name: string | null;
  email: string | null;
  phone: string | null;
  address: string | null;
  linkedin: string | null;
  website: string | null;
  summary: string | null;
  education_json: string | null;
  work_history_json: string | null;
  skills_json: string | null;
  publications_json: string | null;
  grants_json: string | null;
  awards_json: string | null;
  fieldwork_json: string | null;
  species_expertise: string | null;
  field_sites: string | null;
  conservation_philosophy: string | null;
  teaching_experience: string | null;
  cv_file_path: string | null;
  updated_at: string | null;
}

export interface QAPair {
  id: number;
  question: string;
  answer: string;
  tags: string | null;
  created_at: string;
}

export type JobStatus = 'pending' | 'analyzing' | 'needs_input' | 'ready' | 'complete';

export interface JobSummary {
  id: number;
  url: string;
  title: string | null;
  organization: string | null;
  ats_type: string | null;
  status: JobStatus;
  created_at: string;
  analyzed_at: string | null;
}

export interface FormField {
  id: number;
  job_id: number;
  page_number: number;
  field_type: 'text' | 'textarea' | 'select' | 'radio' | 'checkbox' | 'file' | 'date';
  field_label: string | null;
  field_name: string | null;
  field_placeholder: string | null;
  is_required: boolean;
  options_json: string | null;
  proposed_answer: string | null;
  confidence: 'high' | 'medium' | 'low' | 'missing' | null;
  reasoning: string | null;
  source: 'profile' | 'qa_pair' | 'inferred' | 'missing' | null;
  final_answer: string | null;
  user_edited: boolean;
  display_order: number | null;
}

export interface JobDetail extends JobSummary {
  screenshot_path: string | null;
  notes: string | null;
  fields: FormField[];
}

export interface SSEEvent {
  type: 'status' | 'complete' | 'error' | 'needs_action' | 'ping';
  message?: string;
  job_id?: number;
  missing_count?: number;
  action?: 'login' | 'captcha';
}
