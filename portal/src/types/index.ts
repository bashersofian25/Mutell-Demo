export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
}

export interface ApiSuccessResponse<T> {
  success: true;
  data: T;
}

export type UserRole = "super_admin" | "tenant_admin" | "manager" | "viewer";
export type UserStatus = "active" | "suspended" | "invited";
export type SlotStatus = "accepted" | "pending" | "processing" | "evaluated" | "unclear" | "failed";
export type ReportStatus = "generating" | "ready" | "failed";
export type TerminalStatus = "active" | "revoked";
export type AggregationPeriod = "day" | "week" | "month";
export type TenantStatus = "active" | "deleted";
