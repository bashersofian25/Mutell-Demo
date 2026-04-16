"use client";

import { useState } from "react";
import { useAdminUsers, useAdminUpdateUser } from "@/hooks/useAdmin";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import Badge from "@/components/ui/badge/Badge";
import Button from "@/components/ui/button/Button";
import Input from "@/components/form/input/InputField";
import Label from "@/components/form/Label";
import StatusBadge from "@/components/common/StatusBadge";
import Pagination from "@/components/tables/Pagination";
import EmptyState from "@/components/common/EmptyState";
import ActionMenu from "@/components/common/ActionMenu";
import { Modal } from "@/components/ui/modal";
import { useModal } from "@/hooks/useModal";
import { formatRelativeTime } from "@/lib/format";
import { UserResponse } from "@/types/auth";
import { PencilIcon } from "@/icons";

function roleColor(role: string): "primary" | "success" | "warning" | "info" | "light" {
  const map: Record<string, "primary" | "success" | "warning" | "info" | "light"> = {
    super_admin: "primary",
    tenant_admin: "success",
    manager: "warning",
    viewer: "info",
  };
  return map[role] || "light";
}

export default function AdminUsersPage() {
  const [page, setPage] = useState(1);
  const perPage = 20;
  const editModal = useModal();
  const [editingUser, setEditingUser] = useState<UserResponse | null>(null);
  const [editConcurrency, setEditConcurrency] = useState("1");

  const { data, isLoading } = useAdminUsers({ page, per_page: perPage });
  const updateMutation = useAdminUpdateUser();

  const openEdit = (user: UserResponse) => {
    setEditingUser(user);
    setEditConcurrency(String(user.max_concurrent_evaluations ?? 1));
    editModal.openModal();
  };

  const handleUpdate = () => {
    if (!editingUser) return;
    const val = parseInt(editConcurrency, 10);
    if (isNaN(val) || val < 1) return;
    updateMutation.mutate(
      { id: editingUser.id, data: { max_concurrent_evaluations: val } },
      { onSuccess: () => editModal.closeModal() }
    );
  };

  return (
    <div>
      <PageBreadcrumb pageTitle="Users" />

      <Modal isOpen={editModal.isOpen} onClose={editModal.closeModal} className="max-w-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-white/90 mb-6">
          Edit User &mdash; {editingUser?.full_name}
        </h3>
        <form onSubmit={(e) => { e.preventDefault(); handleUpdate(); }} className="space-y-5">
          <div className="space-y-1.5">
            <Label>Email</Label>
            <Input value={editingUser?.email || ""} disabled />
          </div>
          <div className="space-y-1.5">
            <Label>Role</Label>
            <Input value={editingUser?.role?.replace("_", " ") || ""} disabled />
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
              Maximum number of background evaluation processes this user can run simultaneously.
            </p>
          </div>
          <div className="flex gap-3 pt-2">
            <Button type="submit" disabled={updateMutation.isPending}>
              {updateMutation.isPending ? "Saving..." : "Save"}
            </Button>
            <Button variant="outline" onClick={editModal.closeModal}>Cancel</Button>
          </div>
        </form>
      </Modal>

      <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]">
        <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
          <h3 className="text-lg font-semibold text-gray-800 dark:text-white/90">{`All Users${data ? ` (${data.total})` : ""}`}</h3>
        </div>
        <div className="max-w-full overflow-x-auto">
          {isLoading ? (
            <div className="p-6 space-y-3">{[1, 2, 3].map((i) => <div key={i} className="h-12 rounded-lg bg-gray-100 dark:bg-gray-800 animate-pulse" />)}</div>
          ) : !data?.items?.length ? (
            <EmptyState title="No users" description="No users found." />
          ) : (
              <table className="min-w-full">
                <thead className="border-b border-gray-100 dark:border-white/[0.05]">
                  <tr>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Name</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Email</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Role</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Status</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Concurrent Limit</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Last Login</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400 sticky right-0 bg-white dark:bg-gray-900">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-white/[0.05]">
                  {data.items.map((user) => (
                    <tr key={user.id} className="hover:bg-gray-50 dark:hover:bg-white/[0.03]">
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-3">
                          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-50 dark:bg-brand-500/15 text-brand-600 dark:text-brand-400 text-sm font-semibold">
                            {user.full_name?.charAt(0)?.toUpperCase() || "?"}
                          </div>
                          <span className="text-sm font-medium text-gray-800 dark:text-white/90">{user.full_name}</span>
                        </div>
                      </td>
                      <td className="px-5 py-4 text-sm text-gray-500 dark:text-gray-400">{user.email}</td>
                      <td className="px-5 py-4 text-sm">
                        <Badge variant="light" color={roleColor(user.role)}>{user.role.replace("_", " ")}</Badge>
                      </td>
                      <td className="px-5 py-4 text-sm"><StatusBadge status={user.status} /></td>
                      <td className="px-5 py-4 text-sm text-gray-800 dark:text-white/90 font-medium">{user.max_concurrent_evaluations ?? 1}</td>
                      <td className="px-5 py-4 text-sm text-gray-500 dark:text-gray-400">{user.last_login_at ? formatRelativeTime(user.last_login_at) : "Never"}</td>
                      <td className="px-5 py-4 sticky right-0 bg-white dark:bg-gray-900">
                        <ActionMenu
                          items={[
                            { label: "Edit", onClick: () => openEdit(user), icon: <PencilIcon className="h-4 w-4" /> },
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
    </div>
  );
}
