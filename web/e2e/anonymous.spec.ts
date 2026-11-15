import { expect, test } from "@playwright/test";

test("a signed-out dropzone issues no upload request", async ({ page }) => {
  let uploads = 0;
  page.on("request", (request) => {
    if (request.method() === "POST" && request.url().includes("/api/v1/analyses")) uploads += 1;
  });

  await page.goto("/");
  await expect(page.getByText("Analyze your own file")).toBeVisible();
  await expect(page.locator('input[type="file"]')).toHaveCount(0);
  await expect(page.getByRole("link", { name: "create an account" })).toBeVisible();
  expect(uploads).toBe(0);
});
