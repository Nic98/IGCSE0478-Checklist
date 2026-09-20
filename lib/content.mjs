import { readFileSync } from 'node:fs';
import path from 'node:path';
import { validateSamplingDiagram } from './sampling.mjs';

// Astro bundles this module into a temporary directory during prerendering.
// npm runs scripts from the project root; never resolve content from the bundle URL.
export const root = process.env.CHECKLIST_ROOT || process.cwd();
const read = (file) => JSON.parse(readFileSync(path.join(root, file), 'utf8'));
export const catalog = read('content/catalog.json');
export const releaseIds = read('content/releases.json').published;

export function validateReleases(ids, chapters = catalog) {
  if (!Array.isArray(ids) || new Set(ids).size !== ids.length) throw new Error('Published IDs must be a unique array.');
  const allowed = new Set(chapters.flatMap((chapter) => chapter.units.length ? chapter.units.map((unit) => unit.id) : [chapter.id]));
  for (const id of ids) {
    if (typeof id !== 'string' || !allowed.has(id) || !/^\d+(?:\.\d+)?(?:-\d+)?$/.test(id)) throw new Error(`Unknown release ID: ${id}`);
  }
  return ids;
}

export function validateChecklist(document, expectedId, sample = false) {
  const fail = (message) => { throw new Error(`${expectedId}: ${message}`); };
  const required = (value) => typeof value === 'string' && value.trim().length > 0;
  if (document.id !== expectedId) fail('content ID does not match its filename');
  for (const field of ['title', 'label', 'version']) if (!required(document[field])) fail(`missing ${field}`);
  if (document.syllabus !== '2026–2028') fail('unexpected syllabus');
  if (Boolean(document.sample) !== sample) fail('sample content cannot be published as a chapter');
  if (!Array.isArray(document.sections) || !document.sections.length) fail('at least one section is required');
  const sectionIds = new Set();
  const blockIds = new Set();
  const textList = (value) => Array.isArray(value) && value.length > 0 && value.every(required);
  const optionalText = (value) => value === undefined || required(value);
  const integer = (value, max) => Number.isInteger(value) && value >= 0 && value <= max;
  const pageTitles = document.pdfPageTitles;
  if (pageTitles !== undefined && !textList(pageTitles)) fail('PDF page titles must be a non-empty text array');
  let lastPage = 0;
  for (const section of document.sections) {
    if (!required(section.id) || sectionIds.has(section.id)) fail('section IDs must be present and unique');
    sectionIds.add(section.id);
    if (!required(section.title) || !optionalText(section.summary) || !Array.isArray(section.blocks) || !section.blocks.length) fail('sections need a title and knowledge blocks');
    for (const block of section.blocks) {
      if (!required(block.id) || blockIds.has(block.id)) fail('block IDs must be present and unique across the checklist');
      blockIds.add(block.id);
      if (!optionalText(block.hint)) fail('hints must be plain text');
      if (pageTitles) {
        if (!Number.isInteger(block.printPage) || block.printPage < 1 || block.printPage > pageTitles.length || block.printPage < lastPage || block.printPage > lastPage + 1) fail('print pages must cover each PDF page in order');
        lastPage = block.printPage;
      } else if (block.printPage !== undefined) fail('print pages require PDF page titles');
      if (block.type !== 'definition' && !required(block.title)) fail('knowledge blocks need a title');
      switch (block.type) {
        case 'definition':
          if (!required(block.term) || !required(block.text)) fail('definitions need a term and explanation');
          break;
        case 'callout':
          if (!required(block.text)) fail('callouts need an explanation');
          break;
        case 'bullets':
        case 'steps':
        case 'answer-points':
          if (!textList(block.items)) fail('lists need non-empty text items');
          break;
        case 'comparison':
          if (!textList(block.columns) || !Array.isArray(block.rows) || !block.rows.length || block.rows.some((row) => !textList(row) || row.length !== block.columns.length)) fail('comparison rows must match the column headings');
          break;
        case 'example':
          if (!required(block.problem) || !textList(block.steps) || !required(block.result)) fail('examples need a problem, steps and result');
          break;
        case 'equivalence':
          if (!Array.isArray(block.values) || block.values.length < 2 || block.values.some((entry) => !required(entry.label) || !required(entry.value))) fail('equivalences need at least two labelled values');
          break;
        case 'division':
          if (!integer(block.value, 65535) || ![2, 16].includes(block.base)) fail('division needs an unsigned 16-bit value and base 2 or 16');
          break;
        case 'bit-grid':
          if (![8, 16].includes(block.width) || !Array.isArray(block.rows) || !block.rows.length || block.rows.some((row) => !required(row.label) || typeof row.bits !== 'string' || !/^[01]+$/.test(row.bits) || row.bits.length !== block.width)) fail('bit grids need labelled binary rows matching their 8- or 16-bit width');
          if (block.weights !== undefined && (!Array.isArray(block.weights) || block.weights.length !== block.width || block.weights.some((weight) => !Number.isInteger(weight)))) fail('bit-grid weights must match its width');
          if (!optionalText(block.note)) fail('bit-grid notes must be plain text');
          break;
        case 'binary-addition':
          if (block.width !== 8 || !integer(block.a, 255) || !integer(block.b, 255) || !required(block.explanation)) fail('addition needs two unsigned 8-bit values and an explanation');
          break;
        case 'logical-shift':
          if (block.width !== 8 || !integer(block.value, 255) || !['left', 'right'].includes(block.direction) || !Number.isInteger(block.places) || block.places < 1 || block.places > 8 || !required(block.explanation)) fail('logical shifts need an unsigned 8-bit value, direction, 1-8 places and an explanation');
          break;
        case 'sampling-diagram':
          try { validateSamplingDiagram(block); }
          catch (error) { fail(error.message); }
          break;
        default:
          fail(`unsupported knowledge block type: ${block.type}`);
      }
    }
  }
  if (pageTitles && lastPage !== pageTitles.length) fail('every PDF page must contain knowledge blocks');
  if (document.reviewTopics !== undefined) {
    if (!Array.isArray(document.reviewTopics)) fail('review topics must be an array');
    const ids = new Set();
    for (const topic of document.reviewTopics) {
      if (!required(topic.id) || ids.has(topic.id) || !required(topic.label)) fail('review topics need a unique ID and label');
      ids.add(topic.id);
    }
  }
  return document;
}

export function loadPublished() {
  return validateReleases(releaseIds).map((id) => validateChecklist(read(`content/chapters/${id}.json`), id));
}
export function loadSample() {
  return validateChecklist(read('content/samples/layout-preview.json'), 'layout-preview', true);
}
export function loadLocalReview(id) {
  // Validate before constructing a path: only real catalog entries can be reviewed.
  validateReleases([id]);
  const draft = validateChecklist(read(`drafts/${id}.json`), id);
  const review = { ...structuredClone(draft), id: `local-review-${id}`, sample: true };
  return validateChecklist(review, review.id, true);
}
export function availableDocuments(includeSample = false) {
  const documents = loadPublished();
  // Production never examines the selector or opens draft files.
  if (!includeSample) return documents;
  documents.push(loadSample());
  const reviewId = process.env.CHECKLIST_REVIEW_ID;
  if (reviewId) documents.push(loadLocalReview(reviewId));
  return documents;
}
