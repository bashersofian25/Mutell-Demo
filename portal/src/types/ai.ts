export interface AIConfig {
  id: string;
  provider_id: string;
  provider_slug: string;
  provider_name: string;
  model_id: string;
  is_default: boolean;
  custom_prompt: string | null;
  created_at: string;
}

export interface AIConfigListResponse {
  items: AIConfig[];
  total: number;
}

export interface AIConfigCreateRequest {
  provider_id: string;
  model_id: string;
  api_key?: string;
  is_default?: boolean;
  custom_prompt?: string;
}

export interface AIConfigUpdateRequest {
  model_id?: string;
  api_key?: string;
  is_default?: boolean;
  custom_prompt?: string;
}

export interface AIProvider {
  id: string;
  slug: string;
  display_name: string;
  is_active: boolean;
  base_url?: string;
  api_key?: string;
  supported_models?: string[];
}

export interface AIProviderOption {
  id: string;
  slug: string;
  display_name: string;
  supported_models: string[];
}

export interface AIProviderUpdateRequest {
  display_name?: string;
  is_active?: boolean;
  api_key?: string;
  base_url?: string;
}
