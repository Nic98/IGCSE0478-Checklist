import { test, expect } from '@playwright/test';

const base = 'http://127.0.0.1:4322/IGCSE0478-Checklist/';
const production = 'http://127.0.0.1:4323/IGCSE0478-Checklist/';
const chapter = `${base}checklists/local-review-1.2/`;

test.describe('selected Chapter 1.2 local review', () => {
  test.skip(process.env.CHECKLIST_REVIEW_ID !== '1.2', 'Select the ignored 1.2 draft to exercise its local preview.');

  test('sampling graphs and answer blocks remain readable at phone and desktop widths', async ({ page }) => {
    await page.goto(chapter);
    await page.evaluate(() => document.fonts.ready);
    await expect(page.getByRole('heading', { level: 1 })).toHaveText('1.2 Text, sound and images');
    await expect(page.locator('.knowledge-section')).toHaveCount(3);
    await expect(page.locator('#block-image-representation')).toBeVisible();
    await expect(page.locator('#block-image-metadata')).toBeVisible();
    const graphs = page.locator('#block-sampling-comparison svg');
    await expect(graphs).toHaveCount(3);
    // The drawing must show exactly the stored samples, not an extra end-point sample.
    expect(await graphs.evaluateAll((items) => items.map((svg) => svg.querySelectorAll('circle').length))).toEqual([4, 8, 4]);
    for (const width of [320, 390, 680, 1360]) {
      await page.setViewportSize({ width, height: 1000 });
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
      for (const id of ['sampling-comparison', 'sample-rate-effects', 'sample-resolution-effects', 'image-resolution-effects', 'colour-depth-effects']) {
        const block = page.locator(`#block-${id}`);
        expect(await block.evaluate((element) => element.scrollWidth <= element.clientWidth + 1)).toBe(true);
        if (width === 390 || width === 1360) await block.screenshot({ path: `.generated/qa/chapter12-${width}-${id}.png` });
      }
    }
    await page.getByRole('link', { name: '03 Images', exact: true }).click();
    await expect(page).toHaveURL(/#section-images$/);
  });

  test('PDF is downloadable locally while production excludes both chapter drafts', async ({ page, request }) => {
    await page.goto(chapter);
    const href = await page.getByRole('link', { name: /Download PDF/ }).getAttribute('href');
    expect(href).toBe('/IGCSE0478-Checklist/pdfs/local-review-1.2.pdf');
    const pdf = await request.get(`http://127.0.0.1:4322${href}`);
    expect(pdf.ok()).toBe(true);
    expect((await pdf.body()).subarray(0, 5).toString()).toBe('%PDF-');
    for (const id of ['1.1', '1.2']) {
      for (const route of [`checklists/${id}/`, `pdfs/${id}.pdf`, `checklists/local-review-${id}/`, `pdfs/local-review-${id}.pdf`, `drafts/${id}.json`]) {
        expect((await request.get(production + route)).status()).toBe(404);
      }
    }
  });

  test('review choices restore and print only when marked; the graph prints intact', async ({ page }) => {
    await page.goto(chapter);
    await page.evaluate(() => document.fonts.ready);
    const review = page.locator('#optional-assessment');
    await expect(review).toHaveJSProperty('open', false);
    await page.emulateMedia({ media: 'print' });
    await expect(review).toBeHidden();
    await expect(page.locator('#block-sampling-comparison')).toBeVisible();
    await page.pdf({ path: '.generated/qa/chapter12-web-print.pdf', preferCSSPageSize: true });
    await page.emulateMedia({ media: 'screen' });
    await review.locator('summary').click();
    const choice = page.locator('input[data-progress-item="image-metadata"][value="developing"]');
    await choice.check();
    await page.reload();
    await expect(choice).toBeChecked();
    await page.emulateMedia({ media: 'print' });
    await page.evaluate(() => window.dispatchEvent(new Event('beforeprint')));
    await expect(review).toBeVisible();
    expect(await choice.evaluate((element) => getComputedStyle(element.nextElementSibling!, '::after').content)).toContain('✓');
    await expect(page.locator('.summary-toolbar')).toBeHidden();
    await page.pdf({ path: '.generated/qa/chapter12-with-review-print.pdf', preferCSSPageSize: true });
  });
});
