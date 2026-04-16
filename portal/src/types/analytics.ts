export interface ScoreBreakdown {
  overall: number | null;
  sentiment: number | null;
  politeness: number | null;
  compliance: number | null;
  resolution: number | null;
  upselling: number | null;
  response_time: number | null;
  honesty: number | null;
}

export interface TrendPoint {
  period: string;
  overall: number | null;
  sentiment: number | null;
  politeness: number | null;
  compliance: number | null;
}

export interface TagStats {
  tag: string;
  count: number;
  label: string;
}

export interface AnalyticsSummary {
  total_slots: number;
  evaluated_slots: number;
  failed_slots: number;
  pending_slots: number;
  avg_scores: ScoreBreakdown;
  score_trend: TrendPoint[];
  tag_stats: TagStats[];
  total_swearing_incidents: number;
  total_off_topic_incidents: number;
  total_unavailable_items: number;
  unavailable_item_frequency: Record<string, number>;
  language_distribution: Record<string, number>;
  status_distribution: Record<string, number>;
  avg_duration_ms: number | null;
  avg_tokens_used: number | null;
  period_start: string | null;
  period_end: string | null;
}

export interface AnalyticsSummaryParams {
  date_from?: string;
  date_to?: string;
  terminal_id?: string;
}

export type { Aggregation, AggregationListParams, AggregationListResponse } from "./aggregation";
