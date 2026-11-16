import Header from "@/components/Header";
import "./globals.css";

export const metadata = {
  title: "FairLens",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body style={{ margin: 0, minHeight: "100vh", background: "var(--paper, #FAF9F6)",
        color: "var(--ink, #17161A)" }}>
        <Header />
        {children}
      </body>
    </html>
  );
}