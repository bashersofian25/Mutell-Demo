"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/stores/auth-store";
import { useTenantDetail, useUpdateTenant } from "@/hooks/useTenants";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import Button from "@/components/ui/button/Button";
import Input from "@/components/form/input/InputField";
import Label from "@/components/form/Label";

export default function OrganizationSettingsPage() {
  const { user } = useAuth();
  const tenantId = user?.tenant_id || "";
  const { data: tenant, isLoading } = useTenantDetail(tenantId);
  const updateTenant = useUpdateTenant();

  const [name, setName] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [contactPhone, setContactPhone] = useState("");
  const [address, setAddress] = useState("");
  const [slotDuration, setSlotDuration] = useState(300);

  useEffect(() => {
    if (tenant) {
      setName(tenant.name);
      setContactEmail(tenant.contact_email);
      setContactPhone(tenant.contact_phone || "");
      setAddress(tenant.address || "");
      setSlotDuration(tenant.slot_duration_secs);
    }
  }, [tenant]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateTenant.mutate({
      id: tenantId,
      data: {
        name,
        contact_email: contactEmail,
        contact_phone: contactPhone || undefined,
        address: address || undefined,
        slot_duration_secs: slotDuration,
      },
    });
  };

  if (isLoading) {
    return (
      <div>
        <PageBreadcrumb pageTitle="Organization Settings" />
        <div className="h-64 rounded-2xl bg-gray-100 dark:bg-gray-800 animate-pulse" />
      </div>
    );
  }

  return (
    <div>
      <PageBreadcrumb pageTitle="Organization Settings" />

      <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]">
        <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
          <h3 className="text-base font-medium text-gray-800 dark:text-white/90">Organization</h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Manage your organization details and preferences.</p>
        </div>
        <div className="p-4 sm:p-6">
          <form onSubmit={handleSubmit} className="space-y-5 max-w-lg">
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label>Organization Name</Label>
                <Input value={name} onChange={(e) => setName(e.target.value)} required />
              </div>
              <div className="space-y-1.5">
                <Label>Slug</Label>
                <Input value={tenant?.slug || ""} disabled />
              </div>
            </div>
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label>Contact Email</Label>
                <Input type="email" value={contactEmail} onChange={(e) => setContactEmail(e.target.value)} required />
              </div>
              <div className="space-y-1.5">
                <Label>Contact Phone</Label>
                <Input value={contactPhone} onChange={(e) => setContactPhone(e.target.value)} placeholder="+1234567890" />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label>Address</Label>
              <Input value={address} onChange={(e) => setAddress(e.target.value)} placeholder="123 Main St, City" />
            </div>
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label>Timezone</Label>
                <Input value={tenant?.timezone || "UTC"} disabled />
              </div>
              <div className="space-y-1.5">
                <Label>Slot Duration (seconds)</Label>
                <Input type="number" value={String(slotDuration)} onChange={(e) => setSlotDuration(Number(e.target.value))} />
              </div>
            </div>
            <Button type="submit" disabled={updateTenant.isPending}>
              {updateTenant.isPending ? "Saving..." : "Save Changes"}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
