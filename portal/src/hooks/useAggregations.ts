"use client";

import { useQuery } from "@tanstack/react-query";
import { aggregationService } from "@/services/aggregations";
import { AggregationListParams } from "@/types/aggregation";

export function useAggregations(params?: AggregationListParams) {
  return useQuery({
    queryKey: ["aggregations", params],
    queryFn: () => aggregationService.list(params),
  });
}
