import { api } from "@/lib/api";
import { ApiSuccessResponse } from "@/types";
import { DashboardStats } from "@/types/dashboard";

export const dashboardService = {
  getStats: () =>
    api.get<ApiSuccessResponse<DashboardStats>>("/dashboard/stats").then((r) => r.data),
};
