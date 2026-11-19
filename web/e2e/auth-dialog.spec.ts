import { expect, test } from "@playwright/test";

// The app bar's primary action is the sign-in surface for a signed-out visitor
// (UI_UX 5.2, 5.4): it must open the dialog in place, not send them down the page.
test("the app bar action opens the auth dialog and Escape closes it", async ({ page }) => {
  await page.goto("/");
  const dialog = page.locator("dialog.auth-dialog");
  await expect(dialog).toBeHidden();

  await page.locator(".appbar").getByRole("button", { name: "Analyse a file" }).click();
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole("heading", { name: "Sign in" })).toBeVisible();
  await expect(dialog.getByLabel("Email")).toBeFocused();

  await page.keyboard.press("Escape");
  await expect(dialog).toBeHidden();
});

test("the dialog switches to account creation without leaving the page", async ({ page }) => {
  await page.goto("/");
  await page.locator(".appbar").getByRole("button", { name: "Analyse a file" }).click();
  const dialog = page.locator("dialog.auth-dialog");

  await dialog.getByRole("button", { name: "Create one" }).click();
  await expect(dialog.getByRole("heading", { name: "Create an account" })).toBeVisible();
  await expect(dialog.getByLabel("Display name (optional)")).toBeVisible();
  expect(new URL(page.url()).pathname).toBe("/");
});

// v3.3: the reason is named, so a visitor knows whether to sign up or retry.
test("sign-in names an unknown email", async ({ page }) => {
  await page.goto("/");
  await page.locator(".appbar").getByRole("button", { name: "Analyse a file" }).click();
  const dialog = page.locator("dialog.auth-dialog");

  await dialog.getByLabel("Email").fill(`nobody-${Date.now()}@example.com`);
  await dialog.getByLabel("Password").fill("wrong-password-1");
  await dialog.getByRole("button", { name: "Sign in", exact: true }).click();

  await expect(dialog.getByText("No account uses this email")).toBeVisible();
});
