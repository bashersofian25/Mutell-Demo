"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { dashboardService } from "@/services/dashboard";

export function useDashboardStats() {
  return useQuery({
    queryKey: ["dashboard", "stats"],
    queryFn: () => dashboardService.getStats(),
  });
}
