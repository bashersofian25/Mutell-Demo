"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { terminalService } from "@/services/terminals";
import { TerminalCreateRequest, TerminalUpdateRequest } from "@/types/terminal";
import toast from "react-hot-toast";

export function useTerminalList(params?: { page?: number; per_page?: number }) {
  return useQuery({
    queryKey: ["terminals", params],
    queryFn: () => terminalService.list(params),
  });
}

export function useCreateTerminal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: TerminalCreateRequest) => terminalService.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["terminals"] });
      toast.success("Terminal created");
    },
    onError: () => toast.error("Failed to create terminal"),
  });
}

export function useUpdateTerminal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: TerminalUpdateRequest }) =>
      terminalService.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["terminals"] });
      toast.success("Terminal updated");
    },
    onError: () => toast.error("Failed to update terminal"),
  });
}

export function useDeleteTerminal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => terminalService.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["terminals"] });
      toast.success("Terminal deleted");
    },
    onError: () => toast.error("Failed to delete terminal"),
  });
}

export function usePingTerminal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => terminalService.ping(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["terminals"] });
      toast.success("Ping sent successfully");
    },
    onError: () => toast.error("Failed to ping terminal"),
  });
}
