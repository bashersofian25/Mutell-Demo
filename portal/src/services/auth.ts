import { api } from "@/lib/api";
import { LoginResponse, RefreshResponse, ChangePasswordRequest, User, InviteUserRequest, UserResponse, UpdateUserRequest, Permission, PermissionsResponse, PermissionsSchemaResponse, RegisterRequest, GoogleAuthRequest } from "@/types/auth";

export const authService = {
  login: (email: string, password: string) =>
    api.post<LoginResponse>("/auth/login", { email, password }).then((r) => r.data),

  refresh: (refresh_token: string) =>
    api.post<RefreshResponse>("/auth/refresh", { refresh_token }).then((r) => r.data),

  logout: () =>
    api.post("/auth/logout").then((r) => r.data),

  me: () =>
    api.get<User>("/auth/me").then((r) => r.data),

  forgotPassword: (email: string) =>
    api.post("/auth/forgot-password", { email }).then((r) => r.data),

  resetPassword: (token: string, new_password: string) =>
    api.post("/auth/reset-password", { token, new_password }).then((r) => r.data),

  acceptInvite: (token: string, full_name: string, password: string) =>
    api.post<LoginResponse>("/auth/accept-invite", { token, full_name, password }).then((r) => r.data),

  changePassword: (data: ChangePasswordRequest) =>
    api.post("/auth/change-password", data).then((r) => r.data),

  register: (data: RegisterRequest) =>
    api.post<LoginResponse>("/auth/register", data).then((r) => r.data),

  googleAuth: (id_token: string) =>
    api.post<LoginResponse>("/auth/google", { id_token }).then((r) => r.data),
};

export const userService = {
  list: (params?: { page?: number; per_page?: number }) =>
    api.get<{ items: UserResponse[]; total: number }>("/users", { params }).then((r) => r.data),

  invite: (data: InviteUserRequest) =>
    api.post<UserResponse>("/users/invite", data).then((r) => r.data),

  update: (userId: string, data: UpdateUserRequest) =>
    api.patch<UserResponse>(`/users/${userId}`, data).then((r) => r.data),

  delete: (userId: string) =>
    api.delete(`/users/${userId}`).then((r) => r.data),

  setPermissions: (userId: string, permissions: Permission[]) =>
    api.put(`/users/${userId}/permissions`, permissions).then((r) => r.data),

  getPermissions: (userId: string) =>
    api.get<PermissionsResponse>(`/users/${userId}/permissions`).then((r) => r.data),

  getPermissionSchema: () =>
    api.get<PermissionsSchemaResponse>("/users/meta/permissions").then((r) => r.data),
};
