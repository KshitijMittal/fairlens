"use client";

import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

import AuthForm, { type AuthMode } from "@/components/AuthForm";

export interface User {
  id: string;
  email: string;
  display_name: string | null;
}

interface AuthValue {
  user: User | null;
  loading: boolean;
  openAuth: (mode?: AuthMode) => void;
  refresh: () => Promise<void>;
}

const Ctx = createContext<AuthValue | null>(null);

export function useAuth(): AuthValue {
  const value = useContext(Ctx);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}

// One session probe and one sign-in surface for the whole app (UI_UX 5.4, 6.2).
// The dialog is native <dialog>: focus trapping, Escape and the inert background
// come from the browser, so there is no hand-written trap to get wrong.
export default function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [mode, setMode] = useState<AuthMode | null>(null);
  const [closing, setClosing] = useState(false);
  const dialog = useRef<HTMLDialogElement>(null);
  const pathname = usePathname();
  const router = useRouter();

  const refresh = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/me", { credentials: "include", cache: "no-store" });
      setUser(res.ok ? await res.json() : null);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh, pathname]);

  const openAuth = useCallback((next: AuthMode = "signin") => {
    setClosing(false);
    setMode(next);
  }, []);

  useEffect(() => {
    const node = dialog.current;
    if (!node) return;
    if (mode && !node.open) {
      node.showModal();
      // showModal focuses the first focusable element, which is the close
      // button; the email field is where a person actually types.
      node.querySelector<HTMLInputElement>("input")?.focus();
    }
    if (!mode && node.open) node.close();
  }, [mode]);

  // 140 ms is the exit length in globals.css; the element closes once it has played.
  const closeAuth = useCallback(() => {
    setClosing(true);
    window.setTimeout(() => {
      setClosing(false);
      setMode(null);
    }, 140);
  }, []);

  return (
    <Ctx.Provider value={{ user, loading, openAuth, refresh }}>
      {children}
      <dialog
        ref={dialog}
        className="auth-dialog"
        data-closing={closing || undefined}
        aria-labelledby="auth-dialog-title"
        onCancel={(event) => {
          event.preventDefault();
          closeAuth();
        }}
        onClick={(event) => {
          if (event.target === dialog.current) closeAuth();
        }}
      >
        {mode && (
          <div className="auth-dialog__body">
            <div className="auth-dialog__head">
              <h2 id="auth-dialog-title">
                {mode === "signin" ? "Sign in" : "Create an account"}
              </h2>
              <button type="button" className="auth-dialog__close" onClick={closeAuth} aria-label="Close">
                <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
                  <path d="M3 3l10 10M13 3L3 13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              </button>
            </div>
            <p className="small muted auth-dialog__sub">
              {mode === "signin"
                ? "Your analyses stay attached to this account."
                : "An account is only needed to analyse your own files. Samples need none."}
            </p>
            <AuthForm
              mode={mode}
              onSwitch={setMode}
              onSuccess={() => {
                closeAuth();
                refresh();
                router.refresh();
              }}
            />
          </div>
        )}
      </dialog>
    </Ctx.Provider>
  );
}
