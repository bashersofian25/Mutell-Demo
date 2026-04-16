import { api } from "@/lib/api";
import { AggregationListParams, AggregationListResponse } from "@/types/aggregation";

export const aggregationService = {
  list: (params?: AggregationListParams) =>
    api.get<AggregationListResponse>("/aggregations", { params }).then((r) => r.data),
};
