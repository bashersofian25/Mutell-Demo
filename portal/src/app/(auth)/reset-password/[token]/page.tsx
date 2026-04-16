"use client";

import { useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { api } from "@/lib/api";
import Button from "@/components/ui/button/Button";
import Input from "@/components/form/input/InputField";
import Label from "@/components/form/Label";
import toast from "react-hot-toast";

export default function ResetPasswordPage() {
  const { token } = useParams<{ token: string }>();
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    setError("");
    setLoading(true);
    try {
      await api.post("/auth/reset-password", { token, new_password: password });
      toast.success("Password reset successfully");
      router.push("/login");
    } catch {
      setError("Failed to reset password. The link may have expired.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col justify-center w-full lg:w-1/2 h-full p-6 sm:p-8 lg:p-12">
      <div className="w-full max-w-md mx-auto">
        <div className="mb-8">
          <h1 className="text-title-md font-bold text-gray-900 dark:text-white mb-2">
            Reset Password
          </h1>
          <p className="text-gray-500 dark:text-gray-400">
            Enter your new password below
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {error && (
            <div className="rounded-xl border border-error-500 bg-error-50 p-4 dark:border-error-500/30 dark:bg-error-500/15">
              <p className="text-sm text-error-500">{error}</p>
            </div>
          )}
          <div className="space-y-1.5">
            <Label htmlFor="password">New Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="Min. 8 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="confirm">Confirm Password</Label>
            <Input
              id="confirm"
              type="password"
              placeholder="Repeat your password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
          </div>
          <Button type="submit" className="w-full" loading={loading}>
            Reset Password
          </Button>
        </form>
      </div>
    </div>
  );
}
