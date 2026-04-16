import { api } from "@/lib/api";
import { AIConfigListResponse, AIConfigCreateRequest, AIConfig, AIConfigUpdateRequest, AIProviderOption } from "@/types/ai";

export const aiSettingsService = {
  listProviders: () =>
    api.get<AIProviderOption[]>("/settings/ai/providers").then((r) => r.data),

  list: () =>
    api.get<AIConfigListResponse>("/settings/ai").then((r) => r.data),

  create: (data: AIConfigCreateRequest) =>
    api.post<AIConfig>("/settings/ai", data).then((r) => r.data),

  update: (configId: string, data: AIConfigUpdateRequest) =>
    api.patch<AIConfig>(`/settings/ai/${configId}`, data).then((r) => r.data),

  delete: (configId: string) =>
    api.delete(`/settings/ai/${configId}`).then((r) => r.data),
};
