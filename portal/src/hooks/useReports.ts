"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { reportService } from "@/services/reports";
import { ReportCreateRequest } from "@/types/report";
import toast from "react-hot-toast";

export function useReportList(params?: { page?: number; per_page?: number }) {
  return useQuery({
    queryKey: ["reports", params],
    queryFn: () => reportService.list(params),
  });
}

export function useCreateReport() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ReportCreateRequest) => reportService.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["reports"] });
      toast.success("Report generation started");
    },
    onError: () => toast.error("Failed to generate report"),
  });
}

export function useDownloadReport() {
  return useMutation({
    mutationFn: (reportId: string) => reportService.download(reportId),
    onSuccess: (data) => {
      window.open(data.download_url, "_blank");
    },
    onError: () => toast.error("Report not ready for download"),
  });
}

export function useDeleteReport() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => reportService.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["reports"] });
      toast.success("Report deleted");
    },
    onError: () => toast.error("Failed to delete report"),
  });
}
