import { test, expect } from '@playwright/test';

const base = 'http://127.0.0.1:4322/IGCSE0478-Checklist/';
const production = 'http://127.0.0.1:4323/IGCSE0478-Checklist/';
const chapter = `${base}checklists/local-review-1.1/`;

test.describe('selected Chapter 1.1 local review', () => {
  test.skip(process.env.CHECKLIST_REVIEW_ID !== '1.1', 'Select the ignored 1.1 draft to exercise its local preview.');

  test('full chapter diagrams have correct values and a distinct review identity', async ({ page }) => {
    await page.goto(chapter);
    await expect(page.getByRole('heading', { level: 1 })).toHaveText('1.1 Number systems');
    await expect(page.locator('.sample-banner')).toContainText('LOCAL REVIEW');
    await expect(page.locator('.knowledge-section')).toHaveCount(6);
    await expect(page.locator('.calculation-division')).toHaveCount(1);
    await expect(page.locator('.calculation-binary-addition')).toHaveCount(2);
    await expect(page.locator('.calculation-logical-shift')).toHaveCount(4);
    const sums = await page.locator('.addition-total').evaluateAll((rows) => rows.map((row) => Array.from(row.querySelectorAll('td')).map((cell) => cell.textContent?.trim()).join('')));
    expect(sums).toEqual(['001010100', '100101100']);
    const shifted = await page.locator('.shift-diagram .shift-row:last-child .bit-strip').evaluateAll((rows) => rows.map((row) => Array.from(row.children).map((cell) => cell.firstChild?.textContent).join('')));
    expect(shifted).toEqual(['01011000', '10010000', '00001011', '00000011']);
    await page.getByRole('link', { name: '06 Two’s complement', exact: true }).click();
    await expect(page).toHaveURL(/#section-twos-complement$/);
  });

  test('review PDF is downloadable but chapter and review routes remain absent from production', async ({ page, request }) => {
    await page.goto(base);
    await expect(page.locator('a[href$="checklists/local-review-1.1/"]')).toBeVisible();
    await expect(page.locator('a[href$="checklists/1.1/"]')).toHaveCount(0);
    await page.goto(chapter);
    const href = await page.getByRole('link', { name: /Download PDF/ }).getAttribute('href');
    expect(href).toBe('/IGCSE0478-Checklist/pdfs/local-review-1.1.pdf');
    const download = await request.get(`http://127.0.0.1:4322${href}`);
    expect(download.ok()).toBe(true);
    expect((await download.body()).subarray(0, 5).toString()).toBe('%PDF-');
    for (const route of ['checklists/local-review-1.1/', 'pdfs/local-review-1.1.pdf', 'drafts/1.1.json', 'checklists/1.1/', 'pdfs/1.1.pdf']) {
      expect((await request.get(production + route)).status()).toBe(404);
    }
    await page.goto(production);
    await expect(page.locator('a[href*="local-review"]')).toHaveCount(0);
  });

  test('calculation figures fit phone widths and preserve readable weights', async ({ page }) => {
    await page.goto(chapter);
    await page.evaluate(() => document.fonts.ready);
    for (const width of [320, 390, 680, 1360]) {
      await page.setViewportSize({ width, height: 900 });
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
      const overflowingFigures = await page.locator('.calculation-figure').evaluateAll((figures) => figures.filter((figure) => figure.scrollWidth > figure.clientWidth + 1).length);
      expect(overflowingFigures).toBe(0);
      if (width === 390 || width === 1360) {
        for (const id of ['denary-binary-division','denary-hex-division','hex-denary-place-values','sixteen-bit-place-values','addition-worked-example','shift-left-overflow','signed-place-values']) {
          await page.locator(`#block-${id}`).screenshot({ path: `.generated/qa/chapter-${width}-${id}.png` });
        }
      }
    }
  });

  test('chapter review ratings survive reload and print only after selection', async ({ page }) => {
    await page.goto(chapter);
    await page.evaluate(() => document.fonts.ready);
    await expect(page.locator('#optional-assessment')).toHaveJSProperty('open', false);
    await page.emulateMedia({ media: 'print' });
    await expect(page.locator('#optional-assessment')).toBeHidden();
    await page.pdf({ path: '.generated/qa/chapter-web-print.pdf', preferCSSPageSize: true });
    await page.emulateMedia({ media: 'screen' });
    await page.locator('#optional-assessment > summary').click();
    const choice = page.locator('input[data-progress-item="logical-shifts"][value="developing"]');
    await choice.check();
    await page.reload();
    await expect(choice).toBeChecked();
    await page.emulateMedia({ media: 'print' });
    await page.evaluate(() => window.dispatchEvent(new Event('beforeprint')));
    await expect(page.locator('#optional-assessment')).toBeVisible();
    expect(await choice.evaluate((el) => getComputedStyle(el.nextElementSibling!, '::after').content)).toContain('✓');
    await expect(page.locator('.summary-toolbar')).toBeHidden();
    await page.pdf({ path: '.generated/qa/chapter-with-review-print.pdf', preferCSSPageSize: true });
  });
});
