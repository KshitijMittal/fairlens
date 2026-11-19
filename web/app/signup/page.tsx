"use client";

import { useRouter } from "next/navigation";

import AuthForm from "@/components/AuthForm";

export default function SignupPage() {
  const router = useRouter();

  return (
    <main className="auth">
      <h1>Create an account</h1>
      <p className="auth__sub">Use email and password.</p>
      <AuthForm
        mode="signup"
        onSuccess={() => {
          router.push("/");
          router.refresh();
        }}
        onSwitch={() => router.push("/login")}
      />
    </main>
  );
}
