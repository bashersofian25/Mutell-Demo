import { AggregationPeriod } from "./index";

export interface Aggregation {
  id: string;
  tenant_id: string;
  terminal_id: string | null;
  period_type: AggregationPeriod;
  period_start: string;
  period_end: string;
  slot_count: number;
  avg_overall: number | null;
  avg_sentiment: number | null;
  avg_politeness: number | null;
  avg_compliance: number | null;
  avg_resolution: number | null;
  avg_upselling: number | null;
  avg_response_time: number | null;
  avg_honesty: number | null;
  unclear_count: number;
  flag_counts: Record<string, number>;
  computed_at: string;
}

export interface AggregationListParams {
  period_type?: AggregationPeriod;
  period_start?: string;
  period_end?: string;
  terminal_id?: string;
}

export interface AggregationListResponse {
  items: Aggregation[];
  total: number;
}
