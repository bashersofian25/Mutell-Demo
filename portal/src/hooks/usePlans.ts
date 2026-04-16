"use client";

import { useQuery } from "@tanstack/react-query";
import { planService } from "@/services/plans";

export function usePlanList(params?: { page?: number; per_page?: number }) {
  return useQuery({
    queryKey: ["plans", params],
    queryFn: () => planService.list(params),
  });
}

export function usePlanDetail(planId: string) {
  return useQuery({
    queryKey: ["plans", planId],
    queryFn: () => planService.get(planId),
    enabled: !!planId,
  });
}
