"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";

interface User {
  id: string;
  email: string;
  display_name: string | null;
}

export default function Header() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    async function fetchMe() {
      try {
        const res = await fetch("/api/v1/me", { credentials: "include", cache: "no-store" });
        if (res.ok) {
          const data = await res.json();
          setUser(data);
        } else {
          setUser(null);
        }
      } catch {
        setUser(null);
      } finally {
        setLoading(false);
      }
    }
    fetchMe();
  }, [pathname]);

  if (loading) {
    return (
      <header style={{ padding: "16px 24px", borderBottom: "1px solid #E3E0D8" }}>
        <div style={{ maxWidth: 1000, margin: "0 auto", display: "flex", justifyContent: "space-between" }}>
          <span style={{ color: "#8A8794" }}>Loading…</span>
        </div>
      </header>
    );
  }

  return (
    <header style={{ padding: "16px 24px", borderBottom: "1px solid #E3E0D8" }}>
      <div style={{ maxWidth: 1000, margin: "0 auto", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Link href="/" style={{ fontSize: 20, fontWeight: 600, textDecoration: "none", color: "#17161A" }}>
          FairLens
        </Link>
        <nav style={{ display: "flex", gap: 16, alignItems: "center" }}>
          {user ? (
            <>
              <span style={{ color: "#55525C", fontSize: 15 }}>
                {user.display_name || user.email}
              </span>
              <button
                onClick={async () => {
                  await fetch("/api/v1/auth/logout", { method: "POST", credentials: "include" });
                  setUser(null);
                  router.push("/");
                  router.refresh();
                }}
                style={{
                  padding: "8px 16px", borderRadius: 2, border: "1px solid #8C2F2A",
                  background: "#FAF9F6", color: "#8C2F2A", cursor: "pointer", fontSize: 15,
                }}
              >
                Sign out
              </button>
            </>
          ) : (
            <>
              <Link href="/login" style={{ color: "#17161A", textDecoration: "none", fontSize: 15 }}>
                Sign in
              </Link>
              <Link
                href="/signup"
                style={{
                  padding: "8px 16px", borderRadius: 2, border: "1px solid #17161A",
                  background: "#17161A", color: "#FAF9F6", textDecoration: "none", fontSize: 15,
                }}
              >
                Sign up
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}