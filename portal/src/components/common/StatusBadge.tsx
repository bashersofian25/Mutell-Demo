import React from "react";
import Badge from "@/components/ui/badge/Badge";
import { SlotStatus, UserStatus, TerminalStatus, ReportStatus, TenantStatus } from "@/types";

interface StatusBadgeProps {
  status: string;
}

const statusConfig: Record<string, { color: "success" | "error" | "warning" | "info" | "light" | "primary"; label: string }> = {
  active: { color: "success", label: "Active" },
  evaluated: { color: "success", label: "Evaluated" },
  ready: { color: "success", label: "Ready" },
  suspended: { color: "error", label: "Suspended" },
  failed: { color: "error", label: "Failed" },
  revoked: { color: "error", label: "Revoked" },
  deleted: { color: "error", label: "Deleted" },
  pending: { color: "warning", label: "Pending" },
  processing: { color: "info", label: "Processing" },
  generating: { color: "info", label: "Generating" },
  invited: { color: "primary", label: "Invited" },
  unclear: { color: "warning", label: "Unclear" },
  accepted: { color: "info", label: "Accepted" },
};

export default function StatusBadge({ status }: StatusBadgeProps) {
  const config = statusConfig[status] || { color: "light" as const, label: status };
  return (
    <Badge size="sm" color={config.color}>
      {config.label}
    </Badge>
  );
}
