import type { APIRoute } from 'astro';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { availableDocuments, root } from '../../../lib/content.mjs';
import { localPreview, type Checklist } from '../../lib/site';

export function getStaticPaths() {
  return availableDocuments(localPreview).map((document: Checklist) => ({ params: { id: document.id } }));
}

export const GET: APIRoute = async ({ params }) => {
  // Generated files live outside public/, so stale or draft PDFs can never be copied into a build.
  const allowed = availableDocuments(localPreview).some((document: Checklist) => document.id === params.id);
  if (!allowed) return new Response('Not found', { status: 404 });
  const bytes = await readFile(path.join(root, '.generated/pdfs', `${params.id}.pdf`));
  return new Response(new Uint8Array(bytes), {
    headers: { 'Content-Type': 'application/pdf', 'Content-Disposition': `attachment; filename="0478-${params.id}.pdf"` },
  });
};
