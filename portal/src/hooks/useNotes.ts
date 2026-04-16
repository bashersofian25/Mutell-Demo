"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { noteService } from "@/services/notes";
import { NoteCreateRequest, NoteUpdateRequest } from "@/types/note";
import toast from "react-hot-toast";

export function useNotesList(params?: { slot_id?: string; page?: number; per_page?: number }) {
  return useQuery({
    queryKey: ["notes", params],
    queryFn: () => noteService.list(params),
  });
}

export function useCreateNote() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: NoteCreateRequest) => noteService.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notes"] });
      toast.success("Note added");
    },
    onError: () => toast.error("Failed to add note"),
  });
}

export function useUpdateNote() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: NoteUpdateRequest }) =>
      noteService.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notes"] });
      toast.success("Note updated");
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.detail || "Failed to update note";
      toast.error(msg);
    },
  });
}

export function useDeleteNote() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => noteService.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notes"] });
      toast.success("Note deleted");
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.detail || "Failed to delete note";
      toast.error(msg);
    },
  });
}
