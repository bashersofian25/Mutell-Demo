"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { slotService } from "@/services/slots";
import { SlotListParams, BulkReEvaluateRequest } from "@/types/slot";
import toast from "react-hot-toast";

export function useSlotList(params?: SlotListParams) {
  return useQuery({
    queryKey: ["slots", params],
    queryFn: () => slotService.list(params),
  });
}

export function useSlotDetail(slotId: string) {
  return useQuery({
    queryKey: ["slots", slotId],
    queryFn: () => slotService.get(slotId),
    enabled: !!slotId,
  });
}

export function useReEvaluate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (slotId: string) => slotService.reEvaluate(slotId),
    onSuccess: (_, slotId) => {
      qc.invalidateQueries({ queryKey: ["slots", slotId] });
      qc.invalidateQueries({ queryKey: ["slots"] });
      toast.success("Re-evaluation triggered");
    },
    onError: () => toast.error("Failed to trigger re-evaluation"),
  });
}

export function useBulkReEvaluate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: BulkReEvaluateRequest) => slotService.bulkReEvaluate(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["slots"] });
      toast.success("Bulk re-evaluation triggered");
    },
    onError: () => toast.error("Failed to trigger bulk re-evaluation"),
  });
}

export function useEvaluation(slotId: string) {
  return useQuery({
    queryKey: ["evaluations", slotId],
    queryFn: () => slotService.getEvaluation(slotId),
    enabled: !!slotId,
  });
}
