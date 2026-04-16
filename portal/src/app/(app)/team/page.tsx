"use client";

import { useState, useEffect } from "react";
import { useUserList, useInviteUser, useUpdateUser, useDeleteUser, useSetPermissions, useGetPermissions, usePermissionSchema } from "@/hooks/useUsers";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import Button from "@/components/ui/button/Button";
import Input from "@/components/form/input/InputField";
import Label from "@/components/form/Label";
import Select from "@/components/form/Select";
import StatusBadge from "@/components/common/StatusBadge";
import Badge from "@/components/ui/badge/Badge";
import Pagination from "@/components/tables/Pagination";
import EmptyState from "@/components/common/EmptyState";
import ConfirmDialog from "@/components/common/ConfirmDialog";
import ActionMenu from "@/components/common/ActionMenu";
import { Modal } from "@/components/ui/modal";
import { useModal } from "@/hooks/useModal";
import { formatRelativeTime } from "@/lib/format";
import { UserResponse, UserRole } from "@/types/auth";
import { PencilIcon, TrashBinIcon, LockIcon } from "@/icons";
import Switch from "@/components/form/switch/Switch";

function roleColor(role: string): "primary" | "success" | "warning" | "info" | "light" {
  const map: Record<string, "primary" | "success" | "warning" | "info" | "light"> = {
    super_admin: "primary",
    tenant_admin: "success",
    manager: "warning",
    viewer: "info",
  };
  return map[role] || "light";
}

const roleOptions = [
  { value: "viewer", label: "Viewer" },
  { value: "manager", label: "Manager" },
  { value: "tenant_admin", label: "Admin" },
];

const DEFAULT_PERMISSION_KEYS = [
  { key: "export_reports", label: "Export Reports" },
  { key: "view_analytics", label: "View Analytics" },
  { key: "manage_terminals", label: "Manage Terminals" },
  { key: "manage_users", label: "Manage Users" },
  { key: "create_notes", label: "Create Notes" },
  { key: "generate_reports", label: "Generate Reports" },
];

export default function TeamPage() {
  const inviteModal = useModal();
  const editModal = useModal();
  const permissionsModal = useModal();
  const [page, setPage] = useState(1);
  const perPage = 20;

  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteName, setInviteName] = useState("");
  const [inviteRole, setInviteRole] = useState<string>("viewer");

  const [editingUser, setEditingUser] = useState<UserResponse | null>(null);
  const [editName, setEditName] = useState("");
  const [editRole, setEditRole] = useState<string>("");
  const [editConcurrency, setEditConcurrency] = useState("1");
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);

  const [permissionsTarget, setPermissionsTarget] = useState<string | null>(null);
  const [permissionsState, setPermissionsState] = useState<Record<string, boolean>>({});

  const { data, isLoading } = useUserList({ page, per_page: perPage });
  const inviteMutation = useInviteUser();
  const updateMutation = useUpdateUser();
  const deleteMutation = useDeleteUser();
  const permissionsMutation = useSetPermissions();
  const { data: permissionSchema } = usePermissionSchema();
  const { data: fetchedPermissions } = useGetPermissions(permissionsTarget);

  const permissionKeys = permissionSchema?.permissions?.length
    ? permissionSchema.permissions.map((p) => ({ key: p.key, label: p.label }))
    : DEFAULT_PERMISSION_KEYS;

  useEffect(() => {
    if (fetchedPermissions?.permissions && permissionsTarget) {
      const state: Record<string, boolean> = {};
      permissionKeys.forEach((p) => {
        const existing = fetchedPermissions.permissions.find((fp) => fp.permission === p.key);
        state[p.key] = existing?.granted ?? false;
      });
      setPermissionsState(state);
    }
  }, [fetchedPermissions, permissionsTarget]);

  const handleInvite = () => {
    if (!inviteEmail.trim() || !inviteName.trim()) return;
    inviteMutation.mutate(
      { email: inviteEmail, full_name: inviteName, role: inviteRole as UserRole },
      { onSuccess: () => { inviteModal.closeModal(); setInviteEmail(""); setInviteName(""); setInviteRole("viewer"); } }
    );
  };

  const openEdit = (user: UserResponse) => {
    setEditingUser(user);
    setEditName(user.full_name);
    setEditRole(user.role);
    setEditConcurrency(String(user.max_concurrent_evaluations ?? 1));
    editModal.openModal();
  };

  const openPermissions = (userId: string) => {
    setPermissionsTarget(userId);
    permissionsModal.openModal();
  };

  const handleSavePermissions = () => {
    if (!permissionsTarget) return;
    const perms = permissionKeys.map((p) => ({
      permission: p.key,
      granted: permissionsState[p.key] ?? false,
    }));
    permissionsMutation.mutate(
      { userId: permissionsTarget, permissions: perms },
      { onSuccess: () => permissionsModal.closeModal() }
    );
  };

  const handleUpdate = () => {
    if (!editingUser) return;
    const concurrency = parseInt(editConcurrency, 10);
    updateMutation.mutate(
      { id: editingUser.id, data: { full_name: editName, role: editRole as UserRole, max_concurrent_evaluations: isNaN(concurrency) || concurrency < 1 ? 1 : concurrency } },
      { onSuccess: () => editModal.closeModal() }
    );
  };

  const handleDelete = () => {
    if (!deleteTarget) return;
    deleteMutation.mutate(deleteTarget, { onSuccess: () => setDeleteTarget(null) });
  };

  return (
    <div>
      <PageBreadcrumb pageTitle="Team" />

      <div className="mb-6">
        <Button onClick={inviteModal.openModal}>Invite Member</Button>
      </div>

      <Modal isOpen={inviteModal.isOpen} onClose={inviteModal.closeModal} className="max-w-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-white/90 mb-6">Invite Team Member</h3>
        <form onSubmit={(e) => { e.preventDefault(); handleInvite(); }} className="space-y-5">
          <div className="space-y-1.5">
            <Label>Full Name</Label>
            <Input placeholder="Jane Smith" value={inviteName} onChange={(e) => setInviteName(e.target.value)} required />
          </div>
          <div className="space-y-1.5">
            <Label>Email</Label>
            <Input type="email" placeholder="colleague@company.com" value={inviteEmail} onChange={(e) => setInviteEmail(e.target.value)} required />
          </div>
          <div className="space-y-1.5">
            <Label>Role</Label>
            <Select options={roleOptions} defaultValue={inviteRole} onChange={setInviteRole} />
          </div>
          <div className="flex gap-3 pt-2">
            <Button type="submit" disabled={inviteMutation.isPending}>{inviteMutation.isPending ? "Inviting..." : "Send Invite"}</Button>
            <Button variant="outline" onClick={inviteModal.closeModal}>Cancel</Button>
          </div>
        </form>
      </Modal>

      <Modal isOpen={editModal.isOpen} onClose={editModal.closeModal} className="max-w-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-white/90 mb-6">Edit Team Member</h3>
        <form onSubmit={(e) => { e.preventDefault(); handleUpdate(); }} className="space-y-5">
          <div className="space-y-1.5">
            <Label>Full Name</Label>
            <Input value={editName} onChange={(e) => setEditName(e.target.value)} required />
          </div>
          <div className="space-y-1.5">
            <Label>Email</Label>
            <Input value={editingUser?.email || ""} disabled />
          </div>
          <div className="space-y-1.5">
            <Label>Role</Label>
            <Select options={roleOptions} defaultValue={editRole} onChange={setEditRole} />
          </div>
          <div className="space-y-1.5">
            <Label>Max Concurrent Evaluations</Label>
            <Input
              type="number"
              min="1"
              value={editConcurrency}
              onChange={(e) => setEditConcurrency(e.target.value)}
            />
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Max background evaluation processes this user can run simultaneously.
            </p>
          </div>
          <div className="flex gap-3 pt-2">
            <Button type="submit" disabled={updateMutation.isPending}>{updateMutation.isPending ? "Saving..." : "Save"}</Button>
            <Button variant="outline" onClick={editModal.closeModal}>Cancel</Button>
          </div>
        </form>
      </Modal>

      <Modal isOpen={permissionsModal.isOpen} onClose={permissionsModal.closeModal} className="max-w-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-white/90 mb-6">Edit Permissions</h3>
        {fetchedPermissions ? (
          <div className="space-y-4">
            {permissionKeys.map((p) => (
              <Switch
                key={p.key}
                label={p.label}
                defaultChecked={permissionsState[p.key] ?? false}
                onChange={(checked) => setPermissionsState((prev) => ({ ...prev, [p.key]: checked }))}
              />
            ))}
          </div>
        ) : (
          <div className="space-y-3">{[1, 2, 3].map((i) => <div key={i} className="h-8 rounded bg-gray-100 dark:bg-gray-800 animate-pulse" />)}</div>
        )}
        <div className="flex gap-3 pt-6">
          <Button onClick={handleSavePermissions} disabled={permissionsMutation.isPending}>
            {permissionsMutation.isPending ? "Saving..." : "Save Permissions"}
          </Button>
          <Button variant="outline" onClick={permissionsModal.closeModal}>Cancel</Button>
        </div>
      </Modal>

      <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]">
        <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
          <h3 className="text-lg font-semibold text-gray-800 dark:text-white/90">Team Members{data ? ` (${data.total})` : ""}</h3>
        </div>
        <div className="max-w-full overflow-x-auto">
          {isLoading ? (
            <div className="p-6 space-y-3">{[1, 2, 3].map((i) => <div key={i} className="h-12 rounded-lg bg-gray-100 dark:bg-gray-800 animate-pulse" />)}</div>
          ) : !data?.items?.length ? (
            <EmptyState
              icon={<svg className="h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" /></svg>}
              title="No team members"
              description="Invite your first team member to get started."
            />
          ) : (
            <table className="min-w-full">
                <thead className="border-b border-gray-100 dark:border-white/[0.05]">
                  <tr>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Name</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Email</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Role</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Status</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Last Login</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400 sticky right-0 bg-white dark:bg-gray-900">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-white/[0.05]">
                  {data.items.map((member) => (
                    <tr key={member.id} className="hover:bg-gray-50 dark:hover:bg-white/[0.03]">
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-3">
                          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-50 dark:bg-brand-500/15 text-brand-600 dark:text-brand-400 text-sm font-semibold">
                            {member.full_name?.charAt(0)?.toUpperCase() || "?"}
                          </div>
                          <span className="text-sm font-medium text-gray-800 dark:text-white/90">{member.full_name}</span>
                        </div>
                      </td>
                      <td className="px-5 py-4 text-sm text-gray-500 dark:text-gray-400">{member.email}</td>
                      <td className="px-5 py-4 text-sm">
                        <Badge variant="light" color={roleColor(member.role)}>{member.role.replace("_", " ")}</Badge>
                      </td>
                      <td className="px-5 py-4 text-sm"><StatusBadge status={member.status} /></td>
                      <td className="px-5 py-4 text-sm text-gray-500 dark:text-gray-400">{member.last_login_at ? formatRelativeTime(member.last_login_at) : "Never"}</td>
                      <td className="px-5 py-4 sticky right-0 bg-white dark:bg-gray-900">
                        <ActionMenu
                          items={[
                            { label: "Edit", onClick: () => openEdit(member), icon: <PencilIcon className="h-4 w-4" /> },
                            { label: "Permissions", onClick: () => openPermissions(member.id), icon: <LockIcon className="h-4 w-4" /> },
                            ...(member.status === "active"
                              ? [{ label: "Suspend", onClick: () => setDeleteTarget(member.id), icon: <TrashBinIcon className="h-4 w-4" />, variant: "danger" as const }]
                              : []),
                          ]}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
          )}
        </div>
        {data && data.total > perPage && (
          <div className="px-6 py-4 border-t border-gray-100 dark:border-gray-800">
            <Pagination currentPage={page} totalPages={Math.ceil(data.total / perPage)} onPageChange={setPage} />
          </div>
        )}
      </div>

      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Suspend User"
        message="Are you sure you want to suspend this user? They will lose access to the platform."
        confirmLabel="Suspend"
        variant="danger"
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
}
