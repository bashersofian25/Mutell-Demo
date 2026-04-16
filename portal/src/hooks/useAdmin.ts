"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { adminService } from "@/services/admin";
import { TenantCreateRequest, TenantUpdateRequest } from "@/types/tenant";
import { PlanCreateRequest, PlanUpdateRequest } from "@/types/plan";
import { AIProviderUpdateRequest } from "@/types/ai";
import { AuditLogParams } from "@/types/audit";
import { UpdateUserRequest } from "@/types/auth";
import toast from "react-hot-toast";

function getErrorMessage(err: any): string {
  return err?.response?.data?.detail || err?.response?.data?.message || "An error occurred";
}

export function useAdminTenants(params?: { page?: number; per_page?: number }) {
  return useQuery({
    queryKey: ["admin", "tenants", params],
    queryFn: () => adminService.tenants.list(params),
  });
}

export function useAdminTenantDetail(tenantId: string) {
  return useQuery({
    queryKey: ["admin", "tenants", tenantId],
    queryFn: () => adminService.tenants.get(tenantId),
    enabled: !!tenantId,
  });
}

export function useAdminCreateTenant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: TenantCreateRequest) => adminService.tenants.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "tenants"] });
      toast.success("Tenant created");
    },
    onError: (err: any) => toast.error(getErrorMessage(err)),
  });
}

export function useAdminUpdateTenant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: TenantUpdateRequest }) =>
      adminService.tenants.update(id, data),
    onSuccess: (_, { id }) => {
      qc.invalidateQueries({ queryKey: ["admin", "tenants"] });
      qc.invalidateQueries({ queryKey: ["admin", "tenants", id] });
      toast.success("Tenant updated");
    },
    onError: () => toast.error("Failed to update tenant"),
  });
}

export function useAdminDeleteTenant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => adminService.tenants.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "tenants"] });
      toast.success("Tenant deleted");
    },
    onError: () => toast.error("Failed to delete tenant"),
  });
}

export function useAdminPlans(params?: { page?: number; per_page?: number }) {
  return useQuery({
    queryKey: ["admin", "plans", params],
    queryFn: () => adminService.plans.list(params),
  });
}

export function useAdminCreatePlan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: PlanCreateRequest) => adminService.plans.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "plans"] });
      toast.success("Plan created");
    },
    onError: () => toast.error("Failed to create plan"),
  });
}

export function useAdminUpdatePlan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: PlanUpdateRequest }) =>
      adminService.plans.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "plans"] });
      toast.success("Plan updated");
    },
    onError: () => toast.error("Failed to update plan"),
  });
}

export function useAdminUsers(params?: { page?: number; per_page?: number }) {
  return useQuery({
    queryKey: ["admin", "users", params],
    queryFn: () => adminService.users.list(params),
  });
}

export function useAdminUpdateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateUserRequest }) =>
      adminService.users.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "users"] });
      toast.success("User updated");
    },
    onError: (err: any) => toast.error(getErrorMessage(err)),
  });
}

export function useAdminAuditLog(params?: AuditLogParams) {
  return useQuery({
    queryKey: ["admin", "audit-log", params],
    queryFn: () => adminService.auditLog.list(params),
  });
}

export function useAdminHealth() {
  return useQuery({
    queryKey: ["admin", "health"],
    queryFn: () => adminService.health.get(),
    refetchInterval: 10000,
  });
}

export function useAdminAIProviders() {
  return useQuery({
    queryKey: ["admin", "ai-providers"],
    queryFn: () => adminService.aiProviders.list(),
  });
}

export function useAdminUpdateAIProvider() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: AIProviderUpdateRequest }) =>
      adminService.aiProviders.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "ai-providers"] });
      toast.success("AI provider updated");
    },
    onError: () => toast.error("Failed to update AI provider"),
  });
}

export function useAdminAddProviderModel() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ providerId, modelId }: { providerId: string; modelId: string }) =>
      adminService.aiProviders.addModel(providerId, modelId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "ai-providers"] });
      toast.success("Model added");
    },
    onError: () => toast.error("Failed to add model"),
  });
}

export function useAdminRemoveProviderModel() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ providerId, modelId }: { providerId: string; modelId: string }) =>
      adminService.aiProviders.removeModel(providerId, modelId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "ai-providers"] });
      toast.success("Model removed");
    },
    onError: () => toast.error("Failed to remove model"),
  });
}
