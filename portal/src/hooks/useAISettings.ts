"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { aiSettingsService } from "@/services/ai-settings";
import { AIConfigCreateRequest, AIConfigUpdateRequest, AIProviderOption } from "@/types/ai";
import toast from "react-hot-toast";

export function useAIProviders() {
  return useQuery({
    queryKey: ["ai-providers"],
    queryFn: () => aiSettingsService.listProviders(),
  });
}

export function useAIConfigs() {
  return useQuery({
    queryKey: ["ai-configs"],
    queryFn: () => aiSettingsService.list(),
  });
}

export function useCreateAIConfig() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: AIConfigCreateRequest) => aiSettingsService.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["ai-configs"] });
      toast.success("AI configuration added");
    },
    onError: () => toast.error("Failed to add AI configuration"),
  });
}

export function useUpdateAIConfig() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: AIConfigUpdateRequest }) =>
      aiSettingsService.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["ai-configs"] });
      toast.success("AI configuration updated");
    },
    onError: () => toast.error("Failed to update AI configuration"),
  });
}

export function useDeleteAIConfig() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => aiSettingsService.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["ai-configs"] });
      toast.success("AI configuration deleted");
    },
    onError: () => toast.error("Failed to delete AI configuration"),
  });
}
