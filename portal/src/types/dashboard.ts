export interface DashboardStats {
  slots_today: number;
  slots_week: number;
  evaluated_today: number;
  failed_today: number;
  pending_evaluations: number;
  active_terminals: number;
  avg_score_week: number | null;
  avg_score_month: number | null;
}
