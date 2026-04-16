"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import Button from "@/components/ui/button/Button";
import Input from "@/components/form/input/InputField";
import Label from "@/components/form/Label";
import toast from "react-hot-toast";

export default function AcceptInvitePage() {
  const { token } = useParams<{ token: string }>();
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const res = await api.post("/auth/accept-invite", {
        token,
        full_name: fullName,
        password,
      });
      localStorage.setItem("access_token", res.data.access_token);
      localStorage.setItem("refresh_token", res.data.refresh_token);
      toast.success("Account created successfully");
      const role = res.data.user?.role;
      window.location.href = role === "super_admin" ? "/admin/dashboard" : "/dashboard";
    } catch {
      setError("Invalid or expired invitation");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col justify-center w-full lg:w-1/2 h-full p-6 sm:p-8 lg:p-12">
      <div className="w-full max-w-md mx-auto">
        <div className="mb-8">
          <h1 className="text-title-md font-bold text-gray-900 dark:text-white mb-2">
            Accept Invitation
          </h1>
          <p className="text-gray-500 dark:text-gray-400">
            Set up your account to get started
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {error && (
            <div className="rounded-xl border border-error-500 bg-error-50 p-4 dark:border-error-500/30 dark:bg-error-500/15">
              <p className="text-sm text-error-500">{error}</p>
            </div>
          )}
          <div className="space-y-1.5">
            <Label htmlFor="name">Full Name</Label>
            <Input
              id="name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="John Doe"
              required
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="Min. 8 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <Button type="submit" className="w-full" loading={loading}>
            Create Account
          </Button>
        </form>
      </div>
    </div>
  );
}
