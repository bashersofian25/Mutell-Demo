"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { toast } from "react-hot-toast";
import { authService } from "@/services/auth";
import Button from "@/components/ui/button/Button";
import Input from "@/components/form/input/InputField";
import Label from "@/components/form/Label";

export default function SignupPage() {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      toast.error("Passwords do not match");
      return;
    }

    if (password.length < 8) {
      toast.error("Password must be at least 8 characters");
      return;
    }

    setLoading(true);
    try {
      const res = await authService.register({
        email,
        full_name: fullName,
        password,
      });
      localStorage.setItem("access_token", res.access_token);
      localStorage.setItem("refresh_token", res.refresh_token);
      toast.success("Account created successfully");
      if (res.user.role === "super_admin") {
        router.push("/admin/dashboard");
      } else {
        router.push("/dashboard");
      }
    } catch (err: any) {
      const msg = err?.response?.data?.detail || "Registration failed. Please try again.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = () => {
    try {
      (window as any).google.accounts.id.initialize({
        client_id: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID,
        callback: async (response: any) => {
          try {
            const res = await authService.googleAuth(response.credential);
            localStorage.setItem("access_token", res.access_token);
            localStorage.setItem("refresh_token", res.refresh_token);
            toast.success("Signed in with Google");
            if (res.user.role === "super_admin") {
              router.push("/admin/dashboard");
            } else {
              router.push("/dashboard");
            }
          } catch {
            toast.error("Google sign-in failed. Please try again.");
          }
        },
      });
      (window as any).google.accounts.id.prompt();
    } catch {
      toast.error("Google Sign-In is not available. Please use email registration.");
    }
  };

  return (
    <div className="flex flex-col justify-center w-full lg:w-1/2 h-full p-6 sm:p-8 lg:p-12">
      <div className="w-full max-w-md mx-auto">
        <div className="mb-8 text-center">
          <div className="mb-5 flex h-44 w-44 items-center justify-center rounded-full border-[3px] border-brand-500/40 bg-brand-50 dark:bg-brand-500/10 p-2 shadow-lg shadow-brand-500/10 mx-auto">
            <img
              src="/mutell-logo.svg"
              alt="Mutell logo"
              className="h-40 w-auto dark:invert"
              loading="lazy"
            />
          </div>
          <h1 className="text-title-md font-bold text-gray-900 dark:text-white mb-2">
            Create Account
          </h1>
          <p className="text-gray-500 dark:text-gray-400">
            Enter your details to get started
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {error && (
            <div className="rounded-xl border border-error-500 bg-error-50 p-4 dark:border-error-500/30 dark:bg-error-500/15">
              <p className="text-sm text-error-500">{error}</p>
            </div>
          )}
          <div className="space-y-1.5">
            <Label htmlFor="fullName">Full Name</Label>
            <Input
              id="fullName"
              type="text"
              placeholder="John Doe"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="you@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="confirmPassword">Confirm Password</Label>
            <Input
              id="confirmPassword"
              type="password"
              placeholder="Confirm your password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
          </div>
          <Button type="submit" className="w-full" loading={loading}>
            Create Account
          </Button>
          <Button
            type="button"
            variant="outline"
            className="w-full"
            onClick={handleGoogleSignIn}
          >
            <svg className="h-5 w-5" viewBox="0 0 24 24">
              <path
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                fill="#4285F4"
              />
              <path
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                fill="#34A853"
              />
              <path
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                fill="#FBBC05"
              />
              <path
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                fill="#EA4335"
              />
            </svg>
            Sign in with Google
          </Button>
          <p className="text-center text-sm text-gray-500 dark:text-gray-400">
            Already have an account?{" "}
            <Link
              href="/login"
              className="text-brand-500 hover:text-brand-600 transition-colors"
            >
              Sign in
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
