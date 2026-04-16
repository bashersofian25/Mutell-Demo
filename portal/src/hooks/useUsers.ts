"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { userService } from "@/services/auth";
import { InviteUserRequest, UpdateUserRequest, Permission } from "@/types/auth";
import toast from "react-hot-toast";

function getErrorMessage(err: any): string {
  return err?.response?.data?.detail || err?.response?.data?.message || "An error occurred";
}

export function useUserList(params?: { page?: number; per_page?: number }) {
  return useQuery({
    queryKey: ["users", params],
    queryFn: () => userService.list(params),
  });
}

export function useInviteUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: InviteUserRequest) => userService.invite(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] });
      toast.success("Invitation sent");
    },
    onError: (err: any) => toast.error(getErrorMessage(err)),
  });
}

export function useUpdateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateUserRequest }) =>
      userService.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] });
      toast.success("User updated");
    },
    onError: (err: any) => toast.error(getErrorMessage(err)),
  });
}

export function useDeleteUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => userService.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] });
      toast.success("User suspended");
    },
    onError: (err: any) => toast.error(getErrorMessage(err)),
  });
}

export function useSetPermissions() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ userId, permissions }: { userId: string; permissions: Permission[] }) =>
      userService.setPermissions(userId, permissions),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] });
      toast.success("Permissions updated");
    },
    onError: () => toast.error("Failed to update permissions"),
  });
}

export function useGetPermissions(userId: string | null) {
  return useQuery({
    queryKey: ["user-permissions", userId],
    queryFn: () => userService.getPermissions(userId!),
    enabled: !!userId,
  });
}

export function usePermissionSchema() {
  return useQuery({
    queryKey: ["permission-schema"],
    queryFn: () => userService.getPermissionSchema(),
  });
}
