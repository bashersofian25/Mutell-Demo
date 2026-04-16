import { api } from "@/lib/api";
import { PaginatedResponse } from "@/types";
import { Slot, SlotDetail, SlotListParams, BulkReEvaluateRequest, Evaluation } from "@/types/slot";

export const slotService = {
  list: (params?: SlotListParams) =>
    api.get<PaginatedResponse<Slot>>("/slots", { params }).then((r) => r.data),

  get: (slotId: string) =>
    api.get<SlotDetail>(`/slots/${slotId}`).then((r) => r.data),

  getEvaluation: (slotId: string) =>
    api.get<Evaluation>(`/evaluations/${slotId}`).then((r) => r.data),

  reEvaluate: (slotId: string) =>
    api.post(`/slots/${slotId}/re-evaluate`).then((r) => r.data),

  bulkReEvaluate: (data: BulkReEvaluateRequest) =>
    api.post("/slots/bulk-re-evaluate", data).then((r) => r.data),
};
