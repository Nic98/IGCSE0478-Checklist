import { readdirSync, readFileSync, existsSync } from 'node:fs';
import path from 'node:path';
import { availableDocuments } from '../lib/content.mjs';

export function verifyBuild(output, includeSample = false) {
  const documents = availableDocuments(includeSample);
  const allowed = new Set(documents.map((document) => document.id));
  const walk = (directory) => readdirSync(directory, { withFileTypes: true }).flatMap((item) => item.isDirectory() ? walk(path.join(directory, item.name)) : [path.join(directory, item.name)]);
  for (const file of walk(output)) {
    const relative = path.relative(output, file).split(path.sep).join('/');
    if (relative.endsWith('.map') || /(^|\/)(drafts|content|samples|releases)(\/|\.json)/.test(relative)) throw new Error(`Private source in build: ${relative}`);
    const page = relative.match(/^checklists\/([^/]+)\/index\.html$/);
    const pdf = relative.match(/^pdfs\/([^/]+)\.pdf$/);
    if ((page && !allowed.has(page[1])) || (pdf && !allowed.has(pdf[1]))) throw new Error(`Unreleased output: ${relative}`);
    if (!includeSample && /\.(html|js|json|css|txt)$/.test(relative) && /layout-preview|local-review-/.test(readFileSync(file, 'utf8'))) throw new Error(`Local preview leaked into production: ${relative}`);
  }
  for (const document of documents) {
    for (const expected of [`checklists/${document.id}/index.html`, `pdfs/${document.id}.pdf`]) {
      if (!existsSync(path.join(output, expected))) throw new Error(`Missing published output: ${expected}`);
    }
  }
  console.log(`Release check passed: ${documents.length} checklist(s), matching HTML and PDF.`);
}
