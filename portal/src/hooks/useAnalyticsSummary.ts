"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsService } from "@/services/analytics";
import { AnalyticsSummaryParams } from "@/types/analytics";

export function useAnalyticsSummary(params?: AnalyticsSummaryParams) {
  return useQuery({
    queryKey: ["analytics-summary", params],
    queryFn: () => analyticsService.summary(params),
  });
}
