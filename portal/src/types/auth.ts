import { UserRole } from "./index";
export type { UserRole };

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  tenant_id?: string;
  avatar_url?: string;
}

export interface UserResponse {
  id: string;
  tenant_id: string;
  email: string;
  full_name: string;
  avatar_url: string | null;
  role: UserRole;
  status: string;
  last_login_at: string | null;
  created_at: string;
  max_concurrent_evaluations: number;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  user: User;
}

export interface RefreshResponse {
  access_token: string;
  token_type: "bearer";
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface InviteUserRequest {
  email: string;
  full_name: string;
  role: UserRole;
}

export interface UpdateUserRequest {
  full_name?: string;
  role?: UserRole;
  status?: string;
  max_concurrent_evaluations?: number;
}

export interface Permission {
  permission: string;
  granted: boolean;
}

export interface PermissionSchemaItem {
  key: string;
  label: string;
  description: string;
}

export interface PermissionsSchemaResponse {
  permissions: PermissionSchemaItem[];
}

export interface PermissionsResponse {
  user_id: string;
  permissions: Permission[];
}

export interface RegisterRequest {
  email: string;
  full_name: string;
  password: string;
  tenant_slug?: string;
}

export interface GoogleAuthRequest {
  id_token: string;
}
