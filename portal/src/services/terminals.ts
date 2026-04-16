import { api } from "@/lib/api";
import { PaginatedResponse } from "@/types";
import { Terminal, TerminalCreateRequest, TerminalCreateResponse, TerminalUpdateRequest } from "@/types/terminal";

export const terminalService = {
  list: (params?: { page?: number; per_page?: number }) =>
    api.get<PaginatedResponse<Terminal>>("/terminals", { params }).then((r) => r.data),

  create: (data: TerminalCreateRequest) =>
    api.post<TerminalCreateResponse>("/terminals", data).then((r) => r.data),

  update: (terminalId: string, data: TerminalUpdateRequest) =>
    api.patch<Terminal>(`/terminals/${terminalId}`, data).then((r) => r.data),

  delete: (terminalId: string) =>
    api.delete(`/terminals/${terminalId}`).then((r) => r.data),

  ping: (terminalId: string) =>
    api.post(`/terminals/${terminalId}/ping`).then((r) => r.data),
};
