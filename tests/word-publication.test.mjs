import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { availableDocuments } from '../lib/content.mjs';
import { verifyBuild } from '../scripts/verify-build.mjs';

function buildFixture(t, preview) {
  const output = mkdtempSync(path.join(tmpdir(), 'checklist-word-publication-'));
  t.after(() => rmSync(output, { recursive: true, force: true }));
  const write = (relative, value = '') => {
    const file = path.join(output, relative);
    mkdirSync(path.dirname(file), { recursive: true });
    writeFileSync(file, value);
  };
  for (const document of availableDocuments(preview)) {
    write(`checklists/${document.id}/index.html`, `<a href="../../pdfs/${document.id}.pdf" download>Download PDF</a>`);
    write(`pdfs/${document.id}.pdf`, '%PDF-1.4');
  }
  write('index.html', '<a href="guide.pdf" download>Download PDF</a>');
  write('guide.pdf', '%PDF-1.4');
  return { output, write };
}

for (const preview of [false, true]) {
  const mode = preview ? 'local preview' : 'production';

  test(`${mode} permits PDF downloads and rejects Word files anywhere in the build`, (t) => {
    const fixture = buildFixture(t, preview);
    assert.doesNotThrow(() => verifyBuild(fixture.output, preview));
    for (const extension of ['doc', 'DOCX', 'docm', 'DotX', 'DOTM']) {
      const filename = `assets/teacher-copy.${extension}`;
      fixture.write(filename);
      assert.throws(() => verifyBuild(fixture.output, preview), /Teacher-only Word file/);
      rmSync(path.join(fixture.output, filename));
    }
  });

  test(`${mode} rejects Word links even when the document is hosted elsewhere`, (t) => {
    const fixture = buildFixture(t, preview);
    for (const anchor of [
      '<a href="https://example.com/teacher.DOCX?version=2#page1">Word</a>',
      "<a href='../teacher.doc'>Word</a>",
      '<a href=/teacher.docm>Word</a>',
      '<A HREF="/teacher.dotx">Word</A>',
      '<a href="/teacher%2Edotm">Word</a>',
      '<a href="/file" download="teacher.docx">Word</a>',
    ]) {
      fixture.write('index.html', anchor);
      assert.throws(() => verifyBuild(fixture.output, preview), /Word download link/);
    }
  });
}
