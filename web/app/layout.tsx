import { cookies } from "next/headers";
import localFont from "next/font/local";

import AuthProvider from "@/components/AuthProvider";
import Header from "@/components/Header";
import "./globals.css";

// Geist Sans is a variable font: one file covers 400, 500 and 600 (UI_UX 3.1).
const sans = localFont({
  src: [{ path: "../fonts/geist-sans-latin-var.woff2", weight: "100 900", style: "normal" }],
  variable: "--font-sans",
  display: "swap",
});
const mono = localFont({
  src: [{ path: "../fonts/geist-mono-latin-400.woff2", weight: "400", style: "normal" }],
  variable: "--font-mono",
  display: "swap",
});

export const metadata = {
  title: "FairLens",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  // Resolved before the first byte of HTML, so there is no theme flash (UI_UX 4.3).
  const theme = cookies().get("theme")?.value;
  const resolved = theme === "light" || theme === "dark" ? theme : undefined;
  return (
    <html lang="en" data-theme={resolved} className={`${sans.variable} ${mono.variable}`}>
      <body>
        <AuthProvider>
          <Header />
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
