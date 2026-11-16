import { expect, test } from "@playwright/test";

import { createRun } from "./run";

const ORIGIN = new URL(process.env.BASE_URL ?? "http://localhost:3000").origin;

test("an explicit dark cookie is in the first byte of HTML", async ({ page, context }) => {
  const result = await createRun(page, "pass");
  await context.addCookies([{ name: "theme", value: "dark", url: ORIGIN }]);

  const raw = await (await page.request.get(`/analysis/${result.id}`)).text();
  expect(raw).toContain('data-theme="dark"');

  await page.goto(`/analysis/${result.id}`);
  await expect(page.locator(".report")).toHaveAttribute("data-theme", "dark");
  const paper = await page.locator(".report").evaluate(
    (node) => getComputedStyle(node).backgroundColor);
  expect(paper).toBe("rgb(20, 18, 15)");
});

test.describe("without JavaScript", () => {
  test.use({ javaScriptEnabled: false });

  test("the theme is resolved and painted on the server", async ({ page }) => {
    const result = await createRun(page, "pass");
    await page.context().addCookies([{ name: "theme", value: "light", url: ORIGIN }]);
    await page.goto(`/analysis/${result.id}`);
    await expect(page.locator(".report")).toHaveAttribute("data-theme", "light");
    const paper = await page.locator(".report").evaluate(
      (node) => getComputedStyle(node).backgroundColor);
    expect(paper).toBe("rgb(250, 249, 246)");
  });
});
