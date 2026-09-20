import { readdirSync, readFileSync, existsSync } from 'node:fs';
import path from 'node:path';
import { availableDocuments } from '../lib/content.mjs';

const wordFile = /\.(?:docx?|docm|dotx|dotm)$/i;
const wordLink = /\.(?:docx?|docm|dotx|dotm)(?:[?#]|$)/i;

function hasWordDownload(html) {
  for (const [tag] of html.matchAll(/<a\b[^>]*>/gi)) {
    for (const attribute of tag.matchAll(/\s(?:href|download)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))/gi)) {
      let value = (attribute[1] ?? attribute[2] ?? attribute[3]).trim();
      // URL-encoded filenames are still downloadable Word documents.
      try { value = decodeURIComponent(value); } catch { /* Keep malformed URLs as authored. */ }
      if (wordLink.test(value)) return true;
    }
  }
  return false;
}

export function verifyBuild(output, includeSample = false) {
  const documents = availableDocuments(includeSample);
  const allowed = new Set(documents.map((document) => document.id));
  const walk = (directory) => readdirSync(directory, { withFileTypes: true }).flatMap((item) => item.isDirectory() ? walk(path.join(directory, item.name)) : [path.join(directory, item.name)]);
  for (const file of walk(output)) {
    const relative = path.relative(output, file).split(path.sep).join('/');
    if (wordFile.test(relative)) throw new Error(`Teacher-only Word file in website build: ${relative}`);
    if (/\.html$/i.test(relative) && hasWordDownload(readFileSync(file, 'utf8'))) throw new Error(`Word download link in website build: ${relative}`);
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
