"use client";

import { useAuth } from "@/stores/auth-store";

export function useIsSuperAdmin() {
  const { user } = useAuth();
  return user?.role === "super_admin";
}

export function useIsTenantAdmin() {
  const { user } = useAuth();
  return user?.role === "super_admin" || user?.role === "tenant_admin";
}

export function useCanManageTeam() {
  const { user } = useAuth();
  if (!user) return false;
  return ["super_admin", "tenant_admin", "manager"].includes(user.role);
}

export function useCanManageTerminals() {
  const { user } = useAuth();
  if (!user) return false;
  return ["super_admin", "tenant_admin"].includes(user.role);
}

export function useCanManageAI() {
  const { user } = useAuth();
  if (!user) return false;
  return ["super_admin", "tenant_admin"].includes(user.role);
}

export function useCanCreateNotes() {
  const { user } = useAuth();
  if (!user) return false;
  return user.role !== "viewer";
}

export function useCanManageReports() {
  const { user } = useAuth();
  if (!user) return false;
  return ["super_admin", "tenant_admin", "manager"].includes(user.role);
}
