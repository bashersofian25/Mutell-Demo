export interface Plan {
  id: string;
  name: string;
  description: string | null;
  max_terminals: number;
  max_users: number;
  max_slots_per_day: number;
  retention_days: number;
  allowed_ai_providers: string[];
  custom_prompt_allowed: boolean;
  report_export_allowed: boolean;
  api_rate_limit_per_min: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PlanCreateRequest {
  name: string;
  description?: string;
  max_terminals?: number;
  max_users?: number;
  max_slots_per_day?: number;
  retention_days?: number;
  allowed_ai_providers?: string[];
  custom_prompt_allowed?: boolean;
  report_export_allowed?: boolean;
  api_rate_limit_per_min?: number;
}

export interface PlanUpdateRequest {
  name?: string;
  description?: string;
  max_terminals?: number;
  max_users?: number;
  max_slots_per_day?: number;
  retention_days?: number;
  allowed_ai_providers?: string[];
  custom_prompt_allowed?: boolean;
  report_export_allowed?: boolean;
  api_rate_limit_per_min?: number;
  is_active?: boolean;
}
