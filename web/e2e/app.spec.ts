import { expect, test } from "@playwright/test";

test("首页可进入难题详情并查看证据", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: /查看Agent 评测闭环/ }).click();
  await expect(page.getByRole("heading", { name: "Agent 评测闭环" })).toBeVisible();
  await page.getByRole("button", { name: /EV-001/ }).click();
  await expect(page.getByRole("dialog", { name: "证据详情" })).toBeVisible();
  await expect(page.getByRole("link", { name: "打开模拟原文" })).toHaveAttribute("rel", "noopener noreferrer");
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog", { name: "证据详情" })).toBeHidden();
});

test("动态难题筛选写入 URL 并在刷新后恢复", async ({ page }) => {
  await page.goto("/problems");
  await page.getByLabel("趋势状态").selectOption("rising");
  await expect(page).toHaveURL(/state=rising/);
  await page.reload();
  await expect(page.getByLabel("趋势状态")).toHaveValue("rising");
  await expect(page.getByRole("link", { name: /工具调用可靠性/ })).toBeVisible();
});

test("快讯类型和证据关键词可以筛选", async ({ page }) => {
  await page.goto("/signals");
  await page.getByRole("button", { name: "招聘", exact: true }).click();
  await expect(page.getByRole("article")).toHaveCount(3);
  await page.goto("/evidence");
  await page.getByPlaceholder("搜索标题、发布方或技能").fill("Evals");
  await expect(page.locator("tbody tr")).toHaveCount(5);
});

test("错误和空数据场景提供明确降级状态", async ({ page }) => {
  await page.goto("/?scenario=empty");
  await expect(page.getByRole("heading", { name: "等待更多可验证信号" })).toBeVisible();
  await page.goto("/problems?scenario=error");
  await expect(page.getByRole("heading", { name: "这一组数据暂时没有加载成功" })).toBeVisible();
  await expect(page.getByRole("button", { name: "重新加载" })).toBeVisible();
});

test("手机尺寸保持单列信息和可用导航", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "mobile", "仅在移动端项目验证");
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /本周值得关注的/ })).toBeVisible();
  await page.getByRole("button", { name: "打开导航" }).click();
  await expect(page.getByRole("link", { name: "动态难题" })).toBeVisible();
});
