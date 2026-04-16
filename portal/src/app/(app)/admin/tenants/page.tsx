"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAdminTenants, useAdminCreateTenant, useAdminUpdateTenant, useAdminDeleteTenant } from "@/hooks/useAdmin";
import { useAdminPlans } from "@/hooks/useAdmin";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import Button from "@/components/ui/button/Button";
import Input from "@/components/form/input/InputField";
import Label from "@/components/form/Label";
import Select from "@/components/form/Select";
import StatusBadge from "@/components/common/StatusBadge";
import Pagination from "@/components/tables/Pagination";
import EmptyState from "@/components/common/EmptyState";
import ConfirmDialog from "@/components/common/ConfirmDialog";
import ActionMenu from "@/components/common/ActionMenu";
import { Modal } from "@/components/ui/modal";
import { useModal } from "@/hooks/useModal";
import { formatRelativeTime, truncate } from "@/lib/format";
import { Tenant } from "@/types/tenant";
import { PencilIcon, TrashBinIcon } from "@/icons";

export default function AdminTenantsPage() {
  const router = useRouter();
  const createModal = useModal();
  const editModal = useModal();
  const [page, setPage] = useState(1);
  const perPage = 20;
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [planId, setPlanId] = useState("");

  const [editingTenant, setEditingTenant] = useState<Tenant | null>(null);
  const [editName, setEditName] = useState("");
  const [editEmail, setEditEmail] = useState("");
  const [editPhone, setEditPhone] = useState("");
  const [editAddress, setEditAddress] = useState("");

  const { data, isLoading } = useAdminTenants({ page, per_page: perPage });
  const { data: plansData } = useAdminPlans();
  const createMutation = useAdminCreateTenant();
  const updateMutation = useAdminUpdateTenant();
  const deleteMutation = useAdminDeleteTenant();

  const planOptions = (plansData?.items || []).map((p) => ({ value: p.id, label: p.name }));

  const handleCreate = () => {
    if (!name.trim() || !slug.trim() || !contactEmail.trim()) return;
    createMutation.mutate(
      { name, slug, contact_email: contactEmail, plan_id: planId || undefined },
      { onSuccess: () => { createModal.closeModal(); setName(""); setSlug(""); setContactEmail(""); setPlanId(""); } }
    );
  };

  const openEdit = (tenant: Tenant) => {
    setEditingTenant(tenant);
    setEditName(tenant.name);
    setEditEmail(tenant.contact_email);
    setEditPhone(tenant.contact_phone || "");
    setEditAddress(tenant.address || "");
    editModal.openModal();
  };

  const handleUpdate = () => {
    if (!editingTenant) return;
    updateMutation.mutate(
      { id: editingTenant.id, data: { name: editName, contact_email: editEmail, contact_phone: editPhone || undefined, address: editAddress || undefined } },
      { onSuccess: () => editModal.closeModal() }
    );
  };

  const handleDelete = () => {
    if (!deleteTarget) return;
    deleteMutation.mutate(deleteTarget, { onSuccess: () => setDeleteTarget(null) });
  };

  return (
    <div>
      <PageBreadcrumb pageTitle="Tenants" />

      <div className="mb-6">
        <Button onClick={createModal.openModal}>Create Tenant</Button>
      </div>

      <Modal isOpen={createModal.isOpen} onClose={createModal.closeModal} className="max-w-lg p-6">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-white/90 mb-6">Create Tenant</h3>
        <div className="space-y-5">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label>Name</Label>
              <Input placeholder="Company Name" value={name} onChange={(e) => setName(e.target.value)} required />
            </div>
            <div className="space-y-1.5">
              <Label>Slug</Label>
              <Input placeholder="company-slug" value={slug} onChange={(e) => setSlug(e.target.value)} required />
            </div>
          </div>
          <div className="space-y-1.5">
            <Label>Contact Email</Label>
            <Input type="email" placeholder="admin@company.com" value={contactEmail} onChange={(e) => setContactEmail(e.target.value)} required />
          </div>
          <div className="space-y-1.5">
            <Label>Plan</Label>
            <Select options={[{ value: "", label: "No plan" }, ...planOptions]} onChange={setPlanId} />
          </div>
          <div className="flex gap-3 pt-2">
            <Button onClick={handleCreate} disabled={createMutation.isPending}>{createMutation.isPending ? "Creating..." : "Create"}</Button>
            <Button variant="outline" onClick={createModal.closeModal}>Cancel</Button>
          </div>
        </div>
      </Modal>

      <Modal isOpen={editModal.isOpen} onClose={editModal.closeModal} className="max-w-lg p-6">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-white/90 mb-6">Edit Tenant</h3>
        <div className="space-y-5">
          <div className="space-y-1.5">
            <Label>Name</Label>
            <Input value={editName} onChange={(e) => setEditName(e.target.value)} required />
          </div>
          <div className="space-y-1.5">
            <Label>Contact Email</Label>
            <Input type="email" value={editEmail} onChange={(e) => setEditEmail(e.target.value)} required />
          </div>
          <div className="space-y-1.5">
            <Label>Contact Phone</Label>
            <Input value={editPhone} onChange={(e) => setEditPhone(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label>Address</Label>
            <Input value={editAddress} onChange={(e) => setEditAddress(e.target.value)} />
          </div>
          <div className="flex gap-3 pt-2">
            <Button onClick={handleUpdate} disabled={updateMutation.isPending}>{updateMutation.isPending ? "Saving..." : "Save"}</Button>
            <Button variant="outline" onClick={editModal.closeModal}>Cancel</Button>
          </div>
        </div>
      </Modal>

      <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]">
        <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
          <h3 className="text-lg font-semibold text-gray-800 dark:text-white/90">{`All Tenants${data ? ` (${data.total})` : ""}`}</h3>
        </div>
        <div className="max-w-full overflow-x-auto">
          {isLoading ? (
            <div className="p-6 space-y-3">{[1, 2, 3].map((i) => <div key={i} className="h-12 rounded-lg bg-gray-100 dark:bg-gray-800 animate-pulse" />)}</div>
          ) : !data?.items?.length ? (
            <EmptyState title="No tenants" description="Create your first tenant to get started." />
          ) : (
              <table className="min-w-full">
                <thead className="border-b border-gray-100 dark:border-white/[0.05]">
                  <tr>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Name</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Slug</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Status</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Contact</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Created</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400 sticky right-0 bg-white dark:bg-gray-900">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-white/[0.05]">
                  {data.items.map((tenant) => (
                    <tr key={tenant.id} className="hover:bg-gray-50 dark:hover:bg-white/[0.03]">
                      <td className="px-5 py-4">
                        <button className="text-sm font-medium text-brand-500 hover:text-brand-600" onClick={() => router.push(`/admin/tenants/${tenant.id}`)}>
                          {tenant.name}
                        </button>
                      </td>
                      <td className="px-5 py-4 text-sm text-gray-500 dark:text-gray-400 font-mono">{tenant.slug}</td>
                      <td className="px-5 py-4 text-sm"><StatusBadge status={tenant.status} /></td>
                      <td className="px-5 py-4 text-sm text-gray-500 dark:text-gray-400">{tenant.contact_email}</td>
                      <td className="px-5 py-4 text-sm text-gray-500 dark:text-gray-400">{formatRelativeTime(tenant.created_at)}</td>
                      <td className="px-5 py-4 sticky right-0 bg-white dark:bg-gray-900">
                        <ActionMenu
                          items={[
                            { label: "Edit", onClick: () => openEdit(tenant), icon: <PencilIcon className="h-4 w-4" /> },
                            { label: "Delete", onClick: () => setDeleteTarget(tenant.id), icon: <TrashBinIcon className="h-4 w-4" />, variant: "danger" as const },
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
        title="Delete Tenant"
        message="Are you sure you want to delete this tenant? This will soft-delete it."
        confirmLabel="Delete"
        variant="danger"
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
}
