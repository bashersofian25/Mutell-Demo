import { TerminalStatus } from "./index";

export interface Terminal {
  id: string;
  tenant_id: string;
  name: string;
  description: string | null;
  api_key_prefix: string;
  location: string | null;
  status: TerminalStatus;
  last_seen_at: string | null;
  created_at: string;
}

export interface TerminalCreateRequest {
  name: string;
  description?: string;
  location?: string;
}

export interface TerminalCreateResponse extends Terminal {
  api_key: string;
}

export interface TerminalUpdateRequest {
  name?: string;
  description?: string;
  location?: string;
}
