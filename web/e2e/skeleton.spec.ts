import { expect, test } from "@playwright/test";

test("a sample click reaches a rendered verdict with no console error", async ({ page }) => {
  const consoleErrors: string[] = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });
  page.on("pageerror", (error) => consoleErrors.push(String(error)));

  await page.goto("/");
  await expect(page.getByTestId("card-scholarship")).toBeVisible();
  await page.getByTestId("run-scholarship").click();

  await page.waitForURL("**/analysis/**");
  await expect(page.getByTestId("verdict-headline")).toHaveText("All five checks passed.");
  for (const code of ["C1", "C2", "C3", "C4", "C5"]) {
    await expect(page.getByTestId(`check-${code}`)).toBeVisible();
  }
  expect(consoleErrors).toEqual([]);
});
