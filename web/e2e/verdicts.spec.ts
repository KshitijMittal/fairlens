import { expect, test } from "@playwright/test";

import { HEADLINES, createRun, type Verdict } from "./run";

const STATES: Verdict[] = ["fail", "warn", "inconclusive", "pass"];

for (const verdict of STATES) {
  test(`${verdict}: its own lead block, the same skeleton`, async ({ page }) => {
    const result = await createRun(page, verdict);
    await page.goto(`/analysis/${result.id}`);

    const banner = page.getByTestId("verdict-banner");
    await expect(banner).toHaveAttribute("data-verdict", verdict);
    await expect(page.getByTestId("verdict-headline")).toHaveText(HEADLINES[verdict]);

    for (const code of ["C1", "C2", "C3", "C4", "C5"]) {
      await expect(page.getByTestId(`check-${code}`)).toBeVisible();
    }
    await expect(page.locator('svg[role="img"]')).toBeVisible();
    await expect(page.getByText("The method", { exact: true })).toBeVisible();

    const rendered = await page.locator("[data-verdict]").evaluateAll(
      (nodes) => nodes.map((node) => node.getAttribute("data-verdict")));
    for (const state of rendered) {
      expect(STATES).toContain(state);
    }
  });
}
