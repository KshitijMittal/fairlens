import { expect, test } from "@playwright/test";

import { createRun } from "./run";

test("every summary figure exists in the technical view and in the payload", async ({ page }) => {
  const result = await createRun(page, "fail");
  const stored = await (await page.request.get(`/api/v1/analyses/${result.id}`)).json();
  await page.goto(`/analysis/${result.id}`);

  await page.getByText("Show the technical view").click();
  const metrics = page.getByTestId("technical-metrics");

  for (const check of stored.checks as { code: string; value: number | null }[]) {
    if (check.value === null) continue;
    const shown = (check.value as number).toFixed(3);
    await expect(page.getByTestId(`figure-${check.code}`)).toHaveText(shown);
    await expect(metrics.getByRole("row").filter({ hasText: check.code })).toContainText(shown);
  }

  const recorded = page.getByRole("table", { name: "Recorded decisions" });
  for (const row of stored.groups.historical as { n: number; selection_rate: number }[]) {
    await expect(recorded).toContainText(String(row.n));
    await expect(recorded).toContainText(row.selection_rate.toFixed(3));
  }

  if (stored.influence?.available) {
    const top = stored.influence.features[0] as { feature: string; value: number };
    const table = page.getByRole("table", { name: /mean absolute shap/i });
    await expect(table).toContainText(top.feature);
    await expect(table).toContainText(top.value.toFixed(3));
  }
});
