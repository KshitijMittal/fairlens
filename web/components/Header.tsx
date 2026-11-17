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
          <span className="faint">Loading…</span>
        </div>
      </header>
    );
  }

  return (
    <header className="site-header">
      <div className="site-header__row">
        <Link href="/" className="site-header__brand">
          FairLens
        </Link>
        <nav>
          {user ? (
            <>
              <span className="site-header__email">{user.display_name || user.email}</span>
              <button
                onClick={async () => {
                  await fetch("/api/v1/auth/logout", { method: "POST", credentials: "include" });
                  setUser(null);
                  router.push("/");
                  router.refresh();
                }}
                className="btn btn--destructive"
              >
                Sign out
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="btn btn--text">
                Sign in
              </Link>
              <Link href="/signup" className="btn btn--primary">
                Sign up
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
