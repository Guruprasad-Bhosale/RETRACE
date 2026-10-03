export interface SystemStatus {
  environment: string;
  service_name: string;
  api_status: string;
  database_status: string;
  redis_status: string;
  storage_backend: string;
  queue_status?: string;
  worker_status?: string;
}

export interface ReadinessHealth {
  status: string;
  database: { healthy?: boolean; status?: string };
  redis: { healthy?: boolean; status?: string };
  storage: { healthy?: boolean; status?: string; backend?: string };
}

export interface Project {
  id: string;
  name: string;
  description?: string | null;
  created_at: string;
  updated_at?: string;
  version_a_url?: string;
  version_b_url?: string;
}

export interface ApplicationVersion {
  id: string;
  name: string;
  base_url: string;
  git_repo_url?: string | null;
  git_commit_hash?: string | null;
  environment_variables?: Record<string, string>;
  created_at: string;
}

export interface AnalysisSession {
  id: string;
  project_id: string;
  version_a: ApplicationVersion;
  version_b: ApplicationVersion;
  status: 'pending' | 'running' | 'analyzing' | 'reproducing' | 'investigating' | 'completed' | 'failed' | 'cancelled';
  config: Record<string, unknown>;
  workflows_explored: number;
  regressions_count: number;
  error_message?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  created_at: string;
  current_phase?: string;
  progress_pct?: number;
}

export interface ApiKeyItem {
  id: string;
  name: string;
  masked_key: string;
  role: string;
  created_at: string;
  expires_at?: string | null;
  is_active: boolean;
}

export * from './investigation.models';
