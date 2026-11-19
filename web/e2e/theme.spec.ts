import { expect, test } from "@playwright/test";

import { createRun } from "./run";

const ORIGIN = new URL(process.env.BASE_URL ?? "http://localhost:3000").origin;

const background = (page: import("@playwright/test").Page) =>
  page.locator("body").evaluate((node) => getComputedStyle(node).backgroundColor);

test("an explicit dark cookie is in the first byte of HTML", async ({ page, context }) => {
  const result = await createRun(page, "pass");
  await context.addCookies([{ name: "theme", value: "dark", url: ORIGIN }]);

  const raw = await (await page.request.get(`/analysis/${result.id}`)).text();
  expect(raw).toContain('data-theme="dark"');

  await page.goto(`/analysis/${result.id}`);
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  expect(await background(page)).toBe("rgb(9, 9, 11)");
});

test.describe("without JavaScript", () => {
  test.use({ javaScriptEnabled: false });

  test("the theme is resolved and painted on the server", async ({ page }) => {
    const result = await createRun(page, "pass");
    await page.context().addCookies([{ name: "theme", value: "light", url: ORIGIN }]);
    await page.goto(`/analysis/${result.id}`);
    await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
    expect(await background(page)).toBe("rgb(250, 250, 250)");
  });
});
