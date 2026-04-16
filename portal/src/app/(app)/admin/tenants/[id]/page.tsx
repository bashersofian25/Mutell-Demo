"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useAdminTenantDetail, useAdminUpdateTenant, useAdminDeleteTenant } from "@/hooks/useAdmin";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import Button from "@/components/ui/button/Button";
import Input from "@/components/form/input/InputField";
import Label from "@/components/form/Label";
import StatusBadge from "@/components/common/StatusBadge";
import ConfirmDialog from "@/components/common/ConfirmDialog";
import { formatRelativeTime, truncate } from "@/lib/format";

export default function TenantDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [deleteConfirm, setDeleteConfirm] = useState(false);

  const { data: tenant, isLoading } = useAdminTenantDetail(id);
  const updateMutation = useAdminUpdateTenant();
  const deleteMutation = useAdminDeleteTenant();

  const [name, setName] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [contactPhone, setContactPhone] = useState("");
  const [address, setAddress] = useState("");
  const [timezone, setTimezone] = useState("");
  const [slotDuration, setSlotDuration] = useState(300);

  useEffect(() => {
    if (tenant) {
      setName(tenant.name);
      setContactEmail(tenant.contact_email);
      setContactPhone(tenant.contact_phone || "");
      setAddress(tenant.address || "");
      setTimezone(tenant.timezone);
      setSlotDuration(tenant.slot_duration_secs);
    }
  }, [tenant]);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    updateMutation.mutate({
      id,
      data: { name, contact_email: contactEmail, contact_phone: contactPhone || undefined, address: address || undefined, slot_duration_secs: slotDuration },
    });
  };

  const handleDelete = () => {
    deleteMutation.mutate(id, { onSuccess: () => router.push("/admin/tenants") });
  };

  if (isLoading) {
    return (
      <div>
        <PageBreadcrumb pageTitle="Loading..." />
        <div className="h-64 rounded-2xl bg-gray-100 dark:bg-gray-800 animate-pulse" />
      </div>
    );
  }

  if (!tenant) {
    return (
      <div>
        <PageBreadcrumb pageTitle="Not Found" />
        <div className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400 mb-4">Tenant not found</p>
          <Button variant="outline" onClick={() => router.push("/admin/tenants")}>Go back</Button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageBreadcrumb pageTitle={tenant.name} />

      <div className="flex items-center justify-between mb-6">
        <Button variant="outline" size="sm" onClick={() => router.push("/admin/tenants")}>
          <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
          Back
        </Button>
        <div className="flex items-center gap-3">
          <StatusBadge status={tenant.status} />
          <Button variant="outline" size="sm" onClick={() => setDeleteConfirm(true)}>Delete</Button>
        </div>
      </div>

      <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]">
        <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
          <h3 className="text-base font-medium text-gray-800 dark:text-white/90">Tenant Settings</h3>
        </div>
        <div className="p-4 sm:p-6">
          <form onSubmit={handleSave} className="space-y-5 max-w-lg">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label>Name</Label>
                <Input value={name} onChange={(e) => setName(e.target.value)} required />
              </div>
              <div className="space-y-1.5">
                <Label>Slug</Label>
                <Input value={tenant.slug} disabled />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label>Contact Email</Label>
                <Input type="email" value={contactEmail} onChange={(e) => setContactEmail(e.target.value)} required />
              </div>
              <div className="space-y-1.5">
                <Label>Contact Phone</Label>
                <Input value={contactPhone} onChange={(e) => setContactPhone(e.target.value)} />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label>Address</Label>
              <Input value={address} onChange={(e) => setAddress(e.target.value)} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label>Timezone</Label>
                <Input value={timezone} disabled />
              </div>
              <div className="space-y-1.5">
                <Label>Slot Duration (secs)</Label>
                <Input type="number" value={String(slotDuration)} onChange={(e) => setSlotDuration(Number(e.target.value))} />
              </div>
            </div>
            <div className="flex items-center gap-3 pt-2">
              <Button type="submit" disabled={updateMutation.isPending}>{updateMutation.isPending ? "Saving..." : "Save Changes"}</Button>
            </div>
          </form>
        </div>
      </div>

      <ConfirmDialog
        isOpen={deleteConfirm}
        onClose={() => setDeleteConfirm(false)}
        onConfirm={handleDelete}
        title="Delete Tenant"
        message={`Are you sure you want to delete "${tenant.name}"? This action will soft-delete the tenant.`}
        confirmLabel="Delete"
        variant="danger"
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
}
