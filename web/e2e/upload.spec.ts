import path from "node:path";
import { expect, test } from "@playwright/test";

test("drop -> confirm -> run -> report, with the URL changing only on result", async ({ page }) => {
  const email = `e2e-${Date.now()}@example.com`;
  const signup = await page.request.post("/api/v1/auth/signup", {
    data: { email, password: "correct-horse-1" },
  });
  expect(signup.ok()).toBeTruthy();

  await page.goto("/");
  const input = page.locator('input[type="file"]');
  await input.setInputFiles(path.join(__dirname, "../../samples/scholarship.csv"));

  await expect(page.getByText("Confirm what this data means")).toBeVisible();
  expect(page.url()).not.toContain("/analysis/");

  await page.getByRole("button", { name: "Run analysis" }).click();
  await page.waitForURL("**/analysis/**", { timeout: 120_000 });
  await expect(page.getByTestId("verdict-headline")).toBeVisible();
});
