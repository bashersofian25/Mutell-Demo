import { api } from "@/lib/api";
import { PaginatedResponse } from "@/types";
import { Plan, PlanCreateRequest, PlanUpdateRequest } from "@/types/plan";

export const planService = {
  list: (params?: { page?: number; per_page?: number }) =>
    api.get<PaginatedResponse<Plan>>("/plans", { params }).then((r) => r.data),

  get: (planId: string) =>
    api.get<Plan>(`/plans/${planId}`).then((r) => r.data),

  create: (data: PlanCreateRequest) =>
    api.post<Plan>("/plans", data).then((r) => r.data),

  update: (planId: string, data: PlanUpdateRequest) =>
    api.patch<Plan>(`/plans/${planId}`, data).then((r) => r.data),
};
