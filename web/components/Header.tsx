"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/AuthProvider";

export default function Header() {
  const { user, loading, openAuth, refresh } = useAuth();
  const router = useRouter();

  return (
    <header className="appbar">
      <div className="appbar__inner">
        <Link href="/" className="brand">
          FairLens
        </Link>
        {!loading && (
          <div className="appbar__tail">
            {user ? (
              <>
                <span className="appbar__user">{user.display_name || user.email}</span>
                <button
                  onClick={async () => {
                    await fetch("/api/v1/auth/logout", { method: "POST", credentials: "include" });
                    await refresh();
                    router.push("/");
                    router.refresh();
                  }}
                  className="btn btn--ghost"
                >
                  Sign out
                </button>
                <Link href="/#analyse" className="btn btn--primary">
                  Analyse a file
                </Link>
              </>
            ) : (
              // Signed out, the primary action *is* sign-in: one control, one
              // meaning, no second ghost button doing the same thing (v3.3).
              <button onClick={() => openAuth("signin")} className="btn btn--primary">
                Analyse a file
              </button>
            )}
          </div>
        )}
      </div>
    </header>
  );
}
