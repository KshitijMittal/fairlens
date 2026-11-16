import { expect, test, type BrowserContext } from "@playwright/test";

import { createRun } from "./run";

const ORIGIN = new URL(process.env.BASE_URL ?? "http://localhost:3000").origin;
const STATES = ["fail", "warn", "inconclusive", "pass"];

async function tokenPairs(context: BrowserContext, page: import("@playwright/test").Page,
                          theme: "light" | "dark", id: string) {
  await context.addCookies([{ name: "theme", value: theme, url: ORIGIN }]);
  await page.goto(`/analysis/${id}`);
  return page.locator(".report").evaluate((node, states) => {
    const style = getComputedStyle(node);
    const token = (name: string) => style.getPropertyValue(`--${name}`).trim();
    return { paper: token("paper"), ink: token("ink"), states: states.map((state) => ({
      state, foreground: token(state), tint: token(`${state}-tint`),
    })) };
  }, STATES);
}

async function ratio(page: import("@playwright/test").Page, background: string,
                     foreground: string) {
  return page.evaluate(([bg, fg]) => {
    const rgb = (hex: string) => {
      const value = parseInt(hex.replace("#", ""), 16);
      return [(value >> 16) & 255, (value >> 8) & 255, value & 255].map((channel) => {
        const c = channel / 255;
        return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
      });
    };
    const luminance = (hex: string) => {
      const [r, g, b] = rgb(hex);
      return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    };
    const [a, b] = [luminance(bg), luminance(fg)].sort((x, y) => y - x);
    return (a + 0.05) / (b + 0.05);
  }, [background, foreground] as const);
}

for (const theme of ["light", "dark"] as const) {
  test(`${theme}: eight verdict pairs and ink on paper reach 4.5:1`, async ({ page, context }) => {
    const result = await createRun(page, "pass");
    const tokens = await tokenPairs(context, page, theme, result.id);

    for (const state of tokens.states) {
      expect(await ratio(page, state.tint, state.foreground), `${state.state} on its tint`)
        .toBeGreaterThanOrEqual(4.5);
      expect(await ratio(page, tokens.paper, state.foreground), `${state.state} on paper`)
        .toBeGreaterThanOrEqual(4.5);
    }
    expect(await ratio(page, tokens.paper, tokens.ink), "ink on paper").toBeGreaterThanOrEqual(4.5);
  });
}
