"use client";

import { useState } from "react";
import { useAuth } from "@/stores/auth-store";
import { useUpdateUser } from "@/hooks/useUsers";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import Button from "@/components/ui/button/Button";
import Input from "@/components/form/input/InputField";
import Label from "@/components/form/Label";
import Badge from "@/components/ui/badge/Badge";

export default function ProfilePage() {
  const { user, updateUser: updateAuthUser } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name || "");
  const updateUser = useUpdateUser();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!user?.id) return;
    updateUser.mutate(
      { id: user.id, data: { full_name: fullName } },
      { onSuccess: () => updateAuthUser({ full_name: fullName }) }
    );
  };

  function roleColor(role: string): "primary" | "success" | "warning" | "info" | "light" {
    const map: Record<string, "primary" | "success" | "warning" | "info" | "light"> = {
      super_admin: "primary",
      tenant_admin: "success",
      manager: "warning",
      viewer: "info",
    };
    return map[role] || "light";
  }

  return (
    <div>
      <PageBreadcrumb pageTitle="Profile" />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-1">
          <div className="rounded-2xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-white/[0.03] text-center">
            <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-brand-50 dark:bg-brand-500/15 mb-4">
              <span className="text-2xl font-bold text-brand-500">
                {user?.full_name?.charAt(0)?.toUpperCase() || "U"}
              </span>
            </div>
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white/90">{user?.full_name}</h3>
            <div className="mt-2">
              <Badge variant="light" color={roleColor(user?.role || "")}>
                {(user?.role || "").replace("_", " ")}
              </Badge>
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-3">{user?.email}</p>
          </div>
        </div>

        <div className="lg:col-span-2">
          <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]">
            <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
              <h3 className="text-base font-medium text-gray-800 dark:text-white/90">Edit Profile</h3>
            </div>
            <div className="p-4 sm:p-6">
              <form onSubmit={handleSubmit} className="space-y-5 max-w-md">
                <div className="space-y-1.5">
                  <Label>Full Name</Label>
                  <Input value={fullName} onChange={(e) => setFullName(e.target.value)} required />
                </div>
                <div className="space-y-1.5">
                  <Label>Email</Label>
                  <Input value={user?.email || ""} disabled />
                </div>
                <div className="space-y-1.5">
                  <Label>Role</Label>
                  <Input value={(user?.role || "").replace("_", " ")} disabled className="capitalize" />
                </div>
                <Button type="submit" disabled={updateUser.isPending}>
                  {updateUser.isPending ? "Saving..." : "Save Changes"}
                </Button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
