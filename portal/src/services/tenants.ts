import { api } from "@/lib/api";
import { PaginatedResponse } from "@/types";
import { Tenant, TenantCreateRequest, TenantUpdateRequest } from "@/types/tenant";

export const tenantService = {
  list: (params?: { page?: number; per_page?: number }) =>
    api.get<PaginatedResponse<Tenant>>("/tenants", { params }).then((r) => r.data),

  get: (tenantId: string) =>
    api.get<Tenant>(`/tenants/${tenantId}`).then((r) => r.data),

  create: (data: TenantCreateRequest) =>
    api.post<Tenant>("/tenants", data).then((r) => r.data),

  update: (tenantId: string, data: TenantUpdateRequest) =>
    api.patch<Tenant>(`/tenants/${tenantId}`, data).then((r) => r.data),

  delete: (tenantId: string) =>
    api.delete(`/tenants/${tenantId}`).then((r) => r.data),
};
