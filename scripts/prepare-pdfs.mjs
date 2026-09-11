import { spawnSync } from 'node:child_process';
import { mkdirSync, existsSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { availableDocuments, root } from '../lib/content.mjs';

export function preparePdfs(includeSample = false) {
  const documents = availableDocuments(includeSample);
  if (!documents.length) return;
  mkdirSync(path.join(root, '.generated/pdfs'), { recursive: true });
  mkdirSync(path.join(root, '.generated/pdf-inputs'), { recursive: true });
  const localPython = path.join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
  const python = process.env.PYTHON || (existsSync(localPython) ? localPython : 'python3');
  for (const document of documents) {
    // Serialize the resolved document, including the local-review ID and sample mark.
    const input = `.generated/pdf-inputs/${document.id}.json`;
    writeFileSync(path.join(root, input), JSON.stringify(document, null, 2) + '\n');
    const output = `.generated/pdfs/${document.id}.pdf`;
    const result = spawnSync(python, ['scripts/generate_pdf.py', '--input', input, '--output', output, '--fonts', 'assets/fonts'], { cwd: root, stdio: 'inherit' });
    if (result.error || result.status !== 0) {
      throw new Error(`Could not generate ${document.id}. Install requirements.txt in .venv, or set PYTHON to a Python interpreter with ReportLab.`, { cause: result.error });
    }
    console.log(`PDF ready: ${document.id}`);
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) preparePdfs(process.argv.includes('--sample'));
