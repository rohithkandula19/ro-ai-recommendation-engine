import { expect, test } from "@playwright/test";

test("login → browse → open a title", async ({ page }) => {
  await page.goto("/login");
  await page.fill('input[type="email"]', "user0@example.com");
  await page.fill('input[type="password"]', "password123");
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/\/browse/);
  await expect(page.locator("text=Recommended For You").first()).toBeVisible();
});

test("search suggest works", async ({ page, context }) => {
  await context.addCookies([]);
  await page.goto("/login");
  await page.fill('input[type="email"]', "user0@example.com");
  await page.fill('input[type="password"]', "password123");
  await page.click('button[type="submit"]');
  await page.goto("/search");
  await page.fill('input[placeholder*="Search"]', "dark");
  await expect(page.locator("text=/Dark/").first()).toBeVisible({ timeout: 5000 });
});

test("mobile nav opens drawer", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/browse");
  await page.click('[aria-label="open menu"]');
  await expect(page.locator('nav a[href="/movies"]')).toBeVisible();
});
