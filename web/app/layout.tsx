import Header from "@/components/Header";

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
      <body style={{ margin: 0, minHeight: "100vh", background: "#FAF9F6", color: "#17161A" }}>
        <Header />
        {children}
      </body>
    </html>
  );
}