import { cookies } from "next/headers";
import localFont from "next/font/local";

const serif = localFont({
  src: [{ path: "../../../fonts/instrument-serif-latin-400-normal.woff2", weight: "400",
    style: "normal" }],
  variable: "--font-serif",
  display: "swap",
});
const sans = localFont({
  src: [
    { path: "../../../fonts/ibm-plex-sans-latin-400-normal.woff2", weight: "400", style: "normal" },
    { path: "../../../fonts/ibm-plex-sans-latin-500-normal.woff2", weight: "500", style: "normal" },
    { path: "../../../fonts/ibm-plex-sans-latin-600-normal.woff2", weight: "600", style: "normal" },
  ],
  variable: "--font-sans",
  display: "swap",
});

export default function ReportLayout({ children }: { children: React.ReactNode }) {
  // Resolved before the first byte of HTML, so there is no theme flash (UI_UX 4.3).
  const theme = cookies().get("theme")?.value;
  const resolved = theme === "light" || theme === "dark" ? theme : undefined;
  return (
    <div className={`${serif.variable} ${sans.variable} report`} data-theme={resolved}>
      {children}
    </div>
  );
}
