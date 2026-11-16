import { expect, test } from "@playwright/test";

import { createRun } from "./run";

test("Inconclusive is never pass-coloured and its checks are never collapsed", async ({ page }) => {
  const result = await createRun(page, "inconclusive");
  await page.goto(`/analysis/${result.id}`);

  const banner = page.getByTestId("verdict-banner");
  await expect(banner).toHaveAttribute("data-verdict", "inconclusive");
  await expect(page.getByTestId("unjudged-checks")).toContainText("Could not judge");

  const unsure = page.locator('[data-testid^="check-"][data-state="inconclusive"]');
  expect(await unsure.count()).toBeGreaterThan(0);
  for (let index = 0; index < await unsure.count(); index += 1) {
    await expect(unsure.nth(index).locator("details")).toHaveAttribute("open", "");
  }

  const tints = await banner.evaluate((node) => {
    const toRgb = (hex: string) => {
      const value = parseInt(hex.replace("#", ""), 16);
      return `rgb(${(value >> 16) & 255}, ${(value >> 8) & 255}, ${value & 255})`;
    };
    const report = node.closest(".report") as HTMLElement;
    const tokens = getComputedStyle(report);
    return {
      painted: getComputedStyle(node).backgroundColor,
      inconclusive: toRgb(tokens.getPropertyValue("--inconclusive-tint")),
      pass: toRgb(tokens.getPropertyValue("--pass-tint")),
    };
  });
  expect(tints.painted).toBe(tints.inconclusive);
  expect(tints.inconclusive).not.toBe(tints.pass);
});
