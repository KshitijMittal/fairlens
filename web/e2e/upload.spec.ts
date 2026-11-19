import path from "node:path";
import { expect, test } from "@playwright/test";

test("drop -> confirm -> run -> report, with the URL changing only on result", async ({ page }) => {
  const email = `e2e-${Date.now()}@example.com`;
  const signup = await page.request.post("/api/v1/auth/signup", {
    data: { email, password: "Correct-horse-1" },
  });
  expect(signup.ok()).toBeTruthy();

  await page.goto("/");
  const input = page.locator('input[type="file"]');
  await input.setInputFiles(path.join(__dirname, "../../samples/scholarship.csv"));

  // Inspect runs a full parse of the file; under parallel workers it can take
  // more than the default five seconds.
  await expect(page.getByText("Confirm what this data means")).toBeVisible({ timeout: 20_000 });
  expect(page.url()).not.toContain("/analysis/");

  await page.getByRole("button", { name: "Run analysis" }).click();
  await page.waitForURL("**/analysis/**", { timeout: 120_000 });
  await expect(page.getByTestId("verdict-headline")).toBeVisible();
});

// RFC-7807-shaped problem responses used to render as "[object Object]".
test("a problem response is shown as its sentence", async ({ page }) => {
  const email = `e2e-problem-${Date.now()}@example.com`;
  const signup = await page.request.post("/api/v1/auth/signup", {
    data: { email, password: "Correct-horse-1" },
  });
  expect(signup.ok()).toBeTruthy();

  await page.route("**/api/v1/analyses/inspect", (route) =>
    route.fulfill({
      status: 422,
      contentType: "application/json",
      body: JSON.stringify({
        detail: {
          type: "urn:fairlens:error:ambiguous_confirmation",
          title: "Cannot auto-detect columns",
          status: 422,
          detail: "No column looks like an outcome.",
          code: "ambiguous_confirmation",
        },
      }),
    }),
  );

  await page.goto("/");
  await page.locator('input[type="file"]').setInputFiles(path.join(__dirname, "../../samples/scholarship.csv"));

  const notice = page.locator(".notice");
  await expect(notice).toHaveText("No column looks like an outcome.");
  await expect(notice).not.toContainText("[object Object]");
});
