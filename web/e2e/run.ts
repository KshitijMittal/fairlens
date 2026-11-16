import fs from "node:fs";
import path from "node:path";
import { expect, type Page } from "@playwright/test";

export type Verdict = "fail" | "warn" | "inconclusive" | "pass";

const FIXTURES: Record<Verdict, { file: string; confirmations: Record<string, string> }> = {
  fail: {
    file: "../../samples/loan_approvals.csv",
    confirmations: { outcome: "decision", positive: "approved", group: "gender" },
  },
  warn: {
    file: "../../samples/hiring_shortlist.csv",
    confirmations: { outcome: "shortlisted", positive: "yes", group: "ethnicity" },
  },
  pass: {
    file: "../../samples/scholarship.csv",
    confirmations: { outcome: "awarded", positive: "yes", group: "region" },
  },
  inconclusive: {
    file: "fixtures/thin_group.csv",
    confirmations: { outcome: "approved", positive: "yes", group: "group" },
  },
};

export const HEADLINES: Record<Verdict, string> = {
  fail: "This data would teach a model to treat people unequally.",
  warn: "This data is usable, but there is something you should read first.",
  inconclusive: "There is not enough here to judge.",
  pass: "All five checks passed.",
};

export async function createRun(page: Page, verdict: Verdict): Promise<{ id: string }> {
  const email = `e2e-${verdict}-${Date.now()}-${Math.floor(Math.random() * 1e6)}@example.com`;
  const signup = await page.request.post("/api/v1/auth/signup", {
    data: { email, password: "Correct-horse-1" },
  });
  expect(signup.ok()).toBeTruthy();

  const { file, confirmations } = FIXTURES[verdict];
  const absolute = path.join(__dirname, file);
  const res = await page.request.post("/api/v1/analyses", {
    multipart: {
      file: { name: path.basename(absolute), mimeType: "text/csv", buffer: fs.readFileSync(absolute) },
      confirmations: JSON.stringify(confirmations),
    },
    timeout: 180_000,
  });
  expect(res.ok()).toBeTruthy();

  const body = await res.text();
  try {
    return JSON.parse(body);
  } catch {
    const result = body.trim().split("\n")
      .map((line) => JSON.parse(line))
      .find((frame) => frame.event === "result");
    expect(result, "stream ends with a result frame").toBeTruthy();
    return result.payload;
  }
}
