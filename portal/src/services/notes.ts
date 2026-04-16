import { api } from "@/lib/api";
import { PaginatedResponse } from "@/types";
import { Note, NoteCreateRequest, NoteUpdateRequest } from "@/types/note";

export const noteService = {
  list: (params?: { slot_id?: string; page?: number; per_page?: number }) =>
    api.get<PaginatedResponse<Note>>("/notes", { params }).then((r) => r.data),

  create: (data: NoteCreateRequest) =>
    api.post<Note>("/notes", data).then((r) => r.data),

  update: (noteId: string, data: NoteUpdateRequest) =>
    api.patch<Note>(`/notes/${noteId}`, data).then((r) => r.data),

  delete: (noteId: string) =>
    api.delete(`/notes/${noteId}`).then((r) => r.data),
};
