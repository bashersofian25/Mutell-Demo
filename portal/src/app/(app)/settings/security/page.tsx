"use client";

import { useState } from "react";
import { authService } from "@/services/auth";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import Button from "@/components/ui/button/Button";
import Input from "@/components/form/input/InputField";
import Label from "@/components/form/Label";
import toast from "react-hot-toast";

export default function SecuritySettingsPage() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword.length < 8) {
      toast.error("New password must be at least 8 characters");
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error("Passwords do not match");
      return;
    }
    setLoading(true);
    try {
      await authService.changePassword({ current_password: currentPassword, new_password: newPassword });
      toast.success("Password changed successfully");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err: any) {
      const msg = err?.response?.data?.detail || "Failed to change password";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <PageBreadcrumb pageTitle="Security" />

      <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]">
        <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
          <h3 className="text-base font-medium text-gray-800 dark:text-white/90">Change Password</h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Update your password to keep your account secure.</p>
        </div>
        <div className="p-4 sm:p-6">
          <form onSubmit={handleSubmit} className="space-y-5 max-w-md">
            <div className="space-y-1.5">
              <Label>Current Password</Label>
              <Input type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} required />
            </div>
            <div className="space-y-1.5">
              <Label>New Password</Label>
              <Input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} placeholder="Min. 8 characters" required />
            </div>
            <div className="space-y-1.5">
              <Label>Confirm New Password</Label>
              <Input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                error={confirmPassword.length > 0 && newPassword !== confirmPassword}
                hint={confirmPassword.length > 0 && newPassword !== confirmPassword ? "Passwords do not match" : ""}
              />
            </div>
            <Button type="submit" disabled={loading}>
              {loading ? "Changing..." : "Change Password"}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
