import { expect, test } from "@playwright/test";

test("a signed-out dropzone issues no upload request", async ({ page }) => {
  let uploads = 0;
  page.on("request", (request) => {
    if (request.method() === "POST" && request.url().includes("/api/v1/analyses")) uploads += 1;
  });

  await page.goto("/");
  await expect(page.getByRole("heading", { name: /Know what your data teaches/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /Drop a CSV or XLSX file here/ })).toBeVisible();
  await expect(page.locator('input[type="file"]')).toHaveCount(0);

  // Signed out, the dropzone is the sign-in door; it must not pick a file.
  await page.getByRole("button", { name: /Drop a CSV or XLSX file here/ }).click();
  await expect(page.locator("dialog.auth-dialog")).toBeVisible();
  expect(uploads).toBe(0);
});
