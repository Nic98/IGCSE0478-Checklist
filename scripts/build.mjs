import { spawnSync } from 'node:child_process';
import { rmSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { root } from '../lib/content.mjs';
import { preparePdfs } from './prepare-pdfs.mjs';
import { verifyBuild } from './verify-build.mjs';

const includeSample = process.argv.includes('--sample');
const output = path.join(root, includeSample ? '.preview-dist' : 'dist');
// Start clean; release removal must remove old HTML and PDFs as well.
rmSync(output, { recursive: true, force: true });
preparePdfs(includeSample);
const astroPackage = JSON.parse(readFileSync(path.join(root, 'node_modules/astro/package.json'), 'utf8'));
const astroBin = typeof astroPackage.bin === 'string' ? astroPackage.bin : astroPackage.bin.astro;
const result = spawnSync(process.execPath, [path.join(root, 'node_modules/astro', astroBin), 'build'], {
  cwd: root, stdio: 'inherit', env: { ...process.env, LOCAL_PREVIEW: String(includeSample) },
});
if (result.error || result.status !== 0) process.exit(result.status || 1);
verifyBuild(output, includeSample);
