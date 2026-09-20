import { test, expect } from '@playwright/test';
import { mkdir } from 'node:fs/promises';

const base = 'http://127.0.0.1:4322/IGCSE0478-Checklist/';
const production = 'http://127.0.0.1:4323/IGCSE0478-Checklist/';
const sample = `${base}checklists/layout-preview/`;

test('production has the full index, but no sample or locked content routes', async ({ page, request }) => {
  await page.goto(production);
  await expect(page.locator('.chapter')).toHaveCount(10);
  await expect(page.locator('a[href*="layout-preview"]')).toHaveCount(0);
  const { releaseIds } = await import('../../lib/content.mjs');
  if (!releaseIds.includes('1.1')) {
    expect((await request.get(`${production}checklists/1.1/`)).status()).toBe(404);
    expect((await request.get(`${production}pdfs/1.1.pdf`)).status()).toBe(404);
  }
  for (const route of ['checklists/layout-preview/', 'pdfs/layout-preview.pdf', 'content/samples/layout-preview.json']) {
    expect((await request.get(production + route)).status()).toBe(404);
  }
  await page.screenshot({ path: '.generated/qa/course-desktop.png', fullPage: true });
});

test('knowledge content is primary and self-assessment is collapsed by default', async ({ page }) => {
  await page.goto(sample);
  await expect(page.locator('.knowledge-content')).toContainText('A base-2 number system using the digits 0 and 1');
  await expect(page.locator('.worked-example')).toHaveCount(2);
  await expect(page.locator('.knowledge-table')).toHaveCount(2);
  await expect(page.locator('.answer-points')).toHaveCount(3);
  await expect(page.locator('.answer-points').first()).toContainText('Explain why computers use binary.');
  await expect(page.locator('.answer-points').first().getByRole('listitem')).toHaveCount(2);
  await expect(page.locator('#optional-assessment')).toHaveJSProperty('open', false);
  await expect(page.locator('input[data-progress-item]').first()).toBeHidden();
  await expect(page.locator('.knowledge-content')).not.toContainText('I can');
  await page.getByRole('link', { name: '02 Converting between representations' }).click();
  await expect(page).toHaveURL(/#section-converting-values$/);
});

test('optional ratings preserve independent choices across a reload', async ({ page }) => {
  await page.goto(sample);
  await page.locator('#optional-assessment > summary').click();
  const first = page.locator('input[data-progress-item="number-bases"][value="confident"]');
  const second = page.locator('input[data-progress-item="binary-to-denary"][value="developing"]');
  await expect(page.locator('input:checked')).toHaveCount(0);
  await first.check();
  await second.check();
  await page.reload();
  await expect(first).toBeChecked();
  await expect(second).toBeChecked();
  await expect(page.locator('input:checked')).toHaveCount(2);
  await page.getByRole('link', { name: 'Course index', exact: true }).click();
  await expect(page).toHaveURL(base);
});

test('storage errors leave self-assessment usable and explain unsaved choices', async ({ page }) => {
  await page.addInitScript(() => {
    Storage.prototype.setItem = () => { throw new DOMException('Storage blocked', 'QuotaExceededError'); };
  });
  await page.goto(sample);
  await page.locator('#optional-assessment > summary').click();
  const radio = page.locator('input[data-progress-item="number-bases"][value="confident"]');
  await radio.check();
  await expect(radio).toBeChecked();
  await expect(page.getByRole('status')).toContainText('cannot be saved');
  await page.reload();
  await expect(radio).not.toBeChecked();
});

test('blocked access to browser storage does not break controls', async ({ page }) => {
  await page.addInitScript(() => { Object.defineProperty(window, 'localStorage', { get() { throw new DOMException('Blocked', 'SecurityError'); } }); });
  await page.goto(sample);
  await page.locator('#optional-assessment > summary').click();
  await expect(page.getByRole('status')).toContainText('could not be read');
  await page.locator('input[data-progress-item="number-bases"][value="developing"]').check();
  await expect(page.locator('input:checked')).toHaveCount(1);
  await expect(page.getByRole('button', { name: 'Print', exact: true })).toBeVisible();
});

test('PDF download, embedded fonts and print selection work under the project path', async ({ page, request }) => {
  await page.goto(sample);
  await page.evaluate(() => document.fonts.ready);
  expect(await page.evaluate(() => document.fonts.check('16px "Source Sans"') && document.fonts.check('16px "Noto Sans SC"'))).toBe(true);
  const href = await page.getByRole('link', { name: /Download PDF/ }).getAttribute('href');
  expect(href).toBe('/IGCSE0478-Checklist/pdfs/layout-preview.pdf');
  const pdf = await request.get(`http://127.0.0.1:4322${href}`);
  expect(pdf.status()).toBe(200);
  expect(pdf.headers()['content-type']).toContain('application/pdf');
  expect((await pdf.body()).subarray(0,5).toString()).toBe('%PDF-');
  await page.locator('#optional-assessment > summary').click();
  const first = page.locator('input[data-progress-item="number-bases"][value="confident"]');
  await first.check();
  await page.locator('#optional-assessment > summary').click();
  await page.emulateMedia({ media: 'print' });
  await page.evaluate(() => window.dispatchEvent(new Event('beforeprint')));
  await expect(page.getByRole('button', { name: 'Print', exact: true })).toBeHidden();
  await expect(page.locator('.site-header')).toBeHidden();
  expect(await first.evaluate((element) => getComputedStyle(element.nextElementSibling!, '::after').content)).toContain('✓');
  await mkdir('.generated/qa', { recursive: true });
  await page.pdf({ path: '.generated/qa/knowledge-with-review-print.pdf', preferCSSPageSize: true });
});

test('mobile and enlarged text keep all content within the viewport', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(base);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: '.generated/qa/course-mobile.png', fullPage: true });
  await page.goto(sample);
  await page.evaluate(() => document.fonts.ready);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
  await page.screenshot({ path: '.generated/qa/sample-mobile.png', fullPage: true });
  await page.setViewportSize({ width: 1360, height: 960 });
  await page.screenshot({ path: '.generated/qa/sample-desktop.png', fullPage: true });
  // Browser zoom reduces the CSS viewport; use a 680px viewport for 200% at 1360px.
  await page.setViewportSize({ width: 680, height: 480 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

test('printing an unmarked summary excludes optional self-assessment', async ({ page }) => {
  await page.goto(sample);
  await page.evaluate(() => document.fonts.ready);
  await page.emulateMedia({ media: 'print' });
  await expect(page.locator('#optional-assessment')).toBeHidden();
  await expect(page.locator('.knowledge-content')).toContainText('The binary sum is 1 0010 1100');
  await page.pdf({ path: '.generated/qa/knowledge-web-print.pdf', preferCSSPageSize: true });
});
