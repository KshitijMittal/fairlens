import { cookies } from "next/headers";
import { notFound } from "next/navigation";

import Report from "@/components/report/Report";
import type { Analysis } from "@/components/report/types";

export default async function AnalysisPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const origin = process.env.API_ORIGIN ?? "http://localhost:7860";
  // Forward the session so a stored analysis is readable by its owner (F8).
  const res = await fetch(`${origin}/v1/analyses/${id}`, {
    cache: "no-store",
    headers: { cookie: cookies().toString() },
  });
  if (!res.ok) {
    notFound();
  }
  const result: Analysis = await res.json();
  return <Report result={result} />;
}
