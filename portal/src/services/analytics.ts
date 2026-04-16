import { api } from "@/lib/api";
import { AnalyticsSummary, AnalyticsSummaryParams } from "@/types/analytics";
import { AggregationListParams, AggregationListResponse } from "@/types/aggregation";

export const analyticsService = {
  summary: (params?: AnalyticsSummaryParams) =>
    api.get<AnalyticsSummary>("/analytics/summary", { params }).then((r) => r.data),

  aggregations: (params?: AggregationListParams) =>
    api.get<AggregationListResponse>("/aggregations", { params }).then((r) => r.data),
};
