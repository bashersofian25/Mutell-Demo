import { SlotStatus } from "./index";

export interface Slot {
  id: string;
  terminal_id: string;
  tenant_id: string;
  started_at: string;
  ended_at: string;
  duration_secs: number;
  language: string | null;
  word_count: number | null;
  status: SlotStatus;
  tags: string[];
  metadata: Record<string, unknown> | null;
  created_at: string;
  score_overall: number | null;
}

export interface SlotDetail extends Slot {
  raw_text: string;
  evaluation: Evaluation | null;
}

export interface Evaluation {
  id: string;
  slot_id: string;
  tenant_id: string;
  ai_provider: string;
  ai_model: string;
  prompt_version: string;
  score_overall: number | null;
  score_sentiment: number | null;
  score_politeness: number | null;
  score_compliance: number | null;
  score_resolution: number | null;
  score_upselling: number | null;
  score_response_time: number | null;
  score_honesty: number | null;
  sentiment_label: string | null;
  language_detected: string | null;
  summary: string | null;
  strengths: string[] | null;
  weaknesses: string[] | null;
  recommendations: string[] | null;
  unclear_items: string[] | null;
  flags: string[] | null;
  unavailable_items: string[] | null;
  swearing_count: number | null;
  swearing_instances: string[] | null;
  off_topic_count: number | null;
  off_topic_segments: string[] | null;
  speaker_segments: { speaker: string; text: string }[] | null;
  tokens_used: number | null;
  evaluation_duration_ms: number | null;
  is_unclear: boolean;
  created_at: string;
}

export interface SlotListParams {
  page?: number;
  per_page?: number;
  terminal_id?: string;
  status?: SlotStatus;
  date_from?: string;
  date_to?: string;
  min_score?: number;
  max_score?: number;
}

export interface BulkReEvaluateRequest {
  slot_ids: string[];
}
