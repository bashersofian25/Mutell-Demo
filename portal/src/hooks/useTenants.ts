"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { tenantService } from "@/services/tenants";
import { TenantCreateRequest, TenantUpdateRequest } from "@/types/tenant";
import toast from "react-hot-toast";

export function useTenantList(params?: { page?: number; per_page?: number }) {
  return useQuery({
    queryKey: ["tenants", params],
    queryFn: () => tenantService.list(params),
  });
}

export function useTenantDetail(tenantId: string) {
  return useQuery({
    queryKey: ["tenants", tenantId],
    queryFn: () => tenantService.get(tenantId),
    enabled: !!tenantId,
  });
}

export function useCreateTenant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: TenantCreateRequest) => tenantService.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tenants"] });
      toast.success("Tenant created");
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.detail || "Failed to create tenant";
      toast.error(msg);
    },
  });
}

export function useUpdateTenant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: TenantUpdateRequest }) =>
      tenantService.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tenants"] });
      toast.success("Tenant updated");
    },
    onError: () => toast.error("Failed to update tenant"),
  });
}

export function useDeleteTenant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => tenantService.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tenants"] });
      toast.success("Tenant deleted");
    },
    onError: () => toast.error("Failed to delete tenant"),
  });
}
