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
      <header className="site-header">
        <div className="site-header__row">
          <span style={{ color: "var(--ink-faint, #8A8794)" }}>Loading…</span>
        </div>
      </header>
    );
  }

  return (
    <header className="site-header">
      <div className="site-header__row">
        <Link href="/" style={{ fontSize: 20, fontWeight: 600, textDecoration: "none",
          color: "var(--ink, #17161A)" }}>
          FairLens
        </Link>
        <nav>
          {user ? (
            <>
              <span className="site-header__email" style={{ color: "var(--ink-muted, #55525C)",
                fontSize: 15 }}>
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
                  padding: "8px 16px", borderRadius: 2,
                  border: "1px solid var(--fail, #8C2F2A)",
                  background: "var(--paper, #FAF9F6)", color: "var(--fail, #8C2F2A)",
                  cursor: "pointer", fontSize: 15, whiteSpace: "nowrap",
                }}
              >
                Sign out
              </button>
            </>
          ) : (
            <>
              <Link href="/login" style={{ color: "var(--ink, #17161A)", textDecoration: "none",
                fontSize: 15 }}>
                Sign in
              </Link>
              <Link
                href="/signup"
                style={{
                  padding: "8px 16px", borderRadius: 2, border: "1px solid var(--ink, #17161A)",
                  background: "var(--ink, #17161A)", color: "var(--paper, #FAF9F6)",
                  textDecoration: "none", fontSize: 15, whiteSpace: "nowrap",
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