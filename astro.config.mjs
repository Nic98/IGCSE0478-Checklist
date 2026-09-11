import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://nic98.github.io',
  base: '/IGCSE0478-Checklist',
  trailingSlash: 'always',
  output: 'static',
  devToolbar: { enabled: false },
  outDir: process.env.LOCAL_PREVIEW === 'true' ? './.preview-dist' : './dist',
  build: { format: 'directory' },
  vite: { build: { sourcemap: false } },
});
