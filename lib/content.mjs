import { readFileSync } from 'node:fs';
import path from 'node:path';

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
  for (const section of document.sections) {
    if (!required(section.id) || sectionIds.has(section.id)) fail('section IDs must be present and unique');
    sectionIds.add(section.id);
    if (!required(section.title) || !optionalText(section.summary) || !Array.isArray(section.blocks) || !section.blocks.length) fail('sections need a title and knowledge blocks');
    for (const block of section.blocks) {
      if (!required(block.id) || blockIds.has(block.id)) fail('block IDs must be present and unique across the checklist');
      blockIds.add(block.id);
      if (!optionalText(block.hint)) fail('hints must be plain text');
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
        default:
          fail(`unsupported knowledge block type: ${block.type}`);
      }
    }
  }
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
