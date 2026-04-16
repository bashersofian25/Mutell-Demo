import { api } from "@/lib/api";
import { PaginatedResponse } from "@/types";
import { Report, ReportCreateRequest, ReportDownloadResponse } from "@/types/report";

export const reportService = {
  list: (params?: { page?: number; per_page?: number }) =>
    api.get<PaginatedResponse<Report>>("/reports", { params }).then((r) => r.data),

  create: (data: ReportCreateRequest) =>
    api.post<Report>("/reports", data).then((r) => r.data),

  download: (reportId: string) =>
    api.get<ReportDownloadResponse>(`/reports/${reportId}/download`).then((r) => r.data),

  delete: (reportId: string) =>
    api.delete(`/reports/${reportId}`).then((r) => r.data),
};
