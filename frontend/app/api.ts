/** API client functions for the frontend. */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ApiResponse<T> {
  data?: T;
  error?: string;
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return { error: errorData.detail || `HTTP ${response.status}` };
    }

    const data = await response.json();
    return { data };
  } catch (error) {
    return { error: error instanceof Error ? error.message : 'Network error' };
  }
}

// Run types
export interface Run {
  id: number;
  task_id: number;
  status: string;
  integrity_score: number;
  violations_count: number;
  created_at: string;
}

export interface RunDetail {
  id: number;
  task_id: number;
  status: string;
  logs: string;
  created_at: string;
  task: {
    id: number;
    task_text: string;
    built_prompt: string;
  };
  integrity: {
    score: number;
    violations: Array<{
      type: string;
      message: string;
      severity: string;
    }>;
    questions: string[];
  };
  diff: string;
  test_summary: {
    status: string;
    passed: boolean;
  };
}

export interface IntegrityMetrics {
  total_runs: number;
  avg_integrity_score: number;
  violations_by_type: Record<string, number>;
  coverage_trend: Array<{
    date: string;
    score: number;
  }>;
  weekly_stats: {
    total_runs: number;
    avg_integrity_score: number;
    violations_count: number;
  };
}

// API functions
export async function listRuns(filters?: {
  status?: string;
  integrity_min?: number;
  date_from?: string;
  date_to?: string;
}): Promise<ApiResponse<Run[]>> {
  const params = new URLSearchParams();
  if (filters?.status) params.append('status', filters.status);
  if (filters?.integrity_min) params.append('integrity_min', filters.integrity_min.toString());
  if (filters?.date_from) params.append('date_from', filters.date_from);
  if (filters?.date_to) params.append('date_to', filters.date_to);

  return apiRequest<Run[]>(`/runs?${params.toString()}`);
}

export async function getRunDetail(id: string): Promise<ApiResponse<RunDetail>> {
  return apiRequest<RunDetail>(`/runs/${id}`);
}

export async function approveRun(
  id: string,
  justification: string
): Promise<ApiResponse<{ message: string; run_id: number; status: string; pr_url?: string }>> {
  const formData = new FormData();
  formData.append('justification', justification);

  return apiRequest(`/runs/${id}/approve`, {
    method: 'POST',
    body: formData,
  });
}

export async function rejectRun(
  id: string,
  reason: string,
  regenerate: boolean = false
): Promise<ApiResponse<{ message: string; run_id: number; status: string; regeneration_queued: boolean }>> {
  const formData = new FormData();
  formData.append('reason', reason);
  formData.append('regenerate', regenerate.toString());

  return apiRequest(`/runs/${id}/reject`, {
    method: 'POST',
    body: formData,
  });
}

export async function getIntegrityMetrics(): Promise<ApiResponse<IntegrityMetrics>> {
  return apiRequest<IntegrityMetrics>('/metrics/integrity');
}

export async function submitIntegrityAnswers(
  id: string,
  answers: string
): Promise<ApiResponse<{ message: string }>> {
  const formData = new FormData();
  formData.append('answers', answers);

  return apiRequest(`/runs/${id}/answers`, {
    method: 'POST',
    body: formData,
  });
} 