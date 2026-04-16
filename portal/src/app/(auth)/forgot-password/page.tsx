"use client";

import { useState } from "react";
import { authService } from "@/services/auth";
import Button from "@/components/ui/button/Button";
import Input from "@/components/form/input/InputField";
import Label from "@/components/form/Label";
import toast from "react-hot-toast";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await authService.forgotPassword(email);
      setSent(true);
      toast.success("Reset link sent");
    } catch {
      toast.error("Failed to send reset link");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col justify-center w-full lg:w-1/2 h-full p-6 sm:p-8 lg:p-12">
      <div className="w-full max-w-md mx-auto">
        <div className="mb-8">
          <h1 className="text-title-md font-bold text-gray-900 dark:text-white mb-2">
            Forgot Password
          </h1>
          <p className="text-gray-500 dark:text-gray-400">
            {sent ? "Check your email" : "Enter your email to receive a reset link"}
          </p>
        </div>

        {sent ? (
          <div className="text-center space-y-4">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-success-50 dark:bg-success-500/15">
              <svg className="h-7 w-7 text-success-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              If the email exists, a reset link has been sent.
            </p>
            <a href="/login" className="inline-block text-sm text-brand-500 hover:text-brand-600">
              Back to sign in
            </a>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <Button type="submit" className="w-full" loading={loading}>
              Send Reset Link
            </Button>
          </form>
        )}
      </div>
    </div>
  );
}
