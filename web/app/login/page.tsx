"use client";

import { useRouter } from "next/navigation";

import AuthForm from "@/components/AuthForm";

export default function LoginPage() {
  const router = useRouter();

  return (
    <main className="auth">
      <h1>Sign in</h1>
      <p className="auth__sub">Use your email and password.</p>
      <AuthForm
        mode="signin"
        onSuccess={() => {
          router.push("/");
          router.refresh();
        }}
        onSwitch={() => router.push("/signup")}
      />
    </main>
  );
}
