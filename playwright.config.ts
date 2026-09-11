import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/browser',
  outputDir: '.generated/browser-results',
  fullyParallel: true,
  workers: 2,
  use: { baseURL: 'http://127.0.0.1:4322/IGCSE0478-Checklist/', browserName: 'chromium', viewport: { width: 1360, height: 960 } },
  webServer: { command: 'node tests/serve-builds.mjs', url: 'http://127.0.0.1:4322/IGCSE0478-Checklist/', reuseExistingServer: false },
});
