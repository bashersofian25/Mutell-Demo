import { TenantStatus } from "./index";

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  logo_url: string | null;
  contact_email: string;
  contact_phone: string | null;
  address: string | null;
  timezone: string;
  status: TenantStatus;
  plan_id: string | null;
  slot_duration_secs: number;
  created_at: string;
  updated_at: string;
}

export interface TenantCreateRequest {
  name: string;
  slug: string;
  contact_email: string;
  contact_phone?: string;
  address?: string;
  timezone?: string;
  plan_id?: string;
  slot_duration_secs?: number;
}

export interface TenantUpdateRequest {
  name?: string;
  contact_email?: string;
  contact_phone?: string;
  address?: string;
  timezone?: string;
  slot_duration_secs?: number;
  plan_id?: string;
}
