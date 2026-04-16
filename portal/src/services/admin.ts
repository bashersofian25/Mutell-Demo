import { api } from "@/lib/api";
import { PaginatedResponse, ApiSuccessResponse } from "@/types";
import { Tenant, TenantCreateRequest, TenantUpdateRequest } from "@/types/tenant";
import { Plan, PlanCreateRequest, PlanUpdateRequest } from "@/types/plan";
import { UserResponse, UpdateUserRequest } from "@/types/auth";
import { AIProvider, AIProviderUpdateRequest } from "@/types/ai";
import { AuditEntry, AuditLogParams, AuditLogResponse } from "@/types/audit";
import { HealthStatus } from "@/types/health";

export const adminService = {
  tenants: {
    list: (params?: { page?: number; per_page?: number }) =>
      api.get<PaginatedResponse<Tenant>>("/admin/tenants", { params }).then((r) => r.data),

    get: (tenantId: string) =>
      api.get<Tenant>(`/admin/tenants/${tenantId}`).then((r) => r.data),

    create: (data: TenantCreateRequest) =>
      api.post<Tenant>("/admin/tenants", data).then((r) => r.data),

    update: (tenantId: string, data: TenantUpdateRequest) =>
      api.patch<Tenant>(`/admin/tenants/${tenantId}`, data).then((r) => r.data),

    delete: (tenantId: string) =>
      api.delete(`/admin/tenants/${tenantId}`).then((r) => r.data),
  },

  plans: {
    list: (params?: { page?: number; per_page?: number }) =>
      api.get<PaginatedResponse<Plan>>("/admin/plans", { params }).then((r) => r.data),

    create: (data: PlanCreateRequest) =>
      api.post<Plan>("/admin/plans", data).then((r) => r.data),

    update: (planId: string, data: PlanUpdateRequest) =>
      api.patch<Plan>(`/admin/plans/${planId}`, data).then((r) => r.data),
  },

  users: {
    list: (params?: { page?: number; per_page?: number }) =>
      api.get<PaginatedResponse<UserResponse>>("/admin/users", { params }).then((r) => r.data),

    update: (userId: string, data: UpdateUserRequest) =>
      api.patch<UserResponse>(`/admin/users/${userId}`, data).then((r) => r.data),
  },

  auditLog: {
    list: (params?: AuditLogParams) =>
      api.get<AuditLogResponse>("/admin/audit-log", { params }).then((r) => r.data),
  },

  health: {
    get: () =>
      api.get<ApiSuccessResponse<HealthStatus>>("/admin/health").then((r) => r.data),
  },

  aiProviders: {
    list: () =>
      api.get<ApiSuccessResponse<AIProvider[]>>("/admin/ai-providers").then((r) => r.data.data),

    update: (providerId: string, data: AIProviderUpdateRequest) =>
      api.patch<ApiSuccessResponse<AIProvider>>(`/admin/ai-providers/${providerId}`, data).then((r) => r.data.data),

    addModel: (providerId: string, modelId: string) =>
      api.post<ApiSuccessResponse<AIProvider>>(`/admin/ai-providers/${providerId}/models`, { model_id: modelId }).then((r) => r.data.data),

    removeModel: (providerId: string, modelId: string) =>
      api.delete<ApiSuccessResponse<AIProvider>>(`/admin/ai-providers/${providerId}/models/${modelId}`).then((r) => r.data.data),
  },
};
