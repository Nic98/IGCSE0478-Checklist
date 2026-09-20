import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, rmSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { catalog, releaseIds, validateReleases, validateChecklist, loadSample, availableDocuments } from '../lib/content.mjs';

test('the archive hierarchy retains 10 chapters and all 22 theory parts', () => {
  assert.equal(catalog.length, 10);
  assert.equal(catalog.slice(0, 6).flatMap((chapter) => chapter.units).length, 22);
  assert.deepEqual(catalog[2].units.map((unit) => unit.id), ['3.1-1','3.1-2','3.2-1','3.2-2','3.3-1','3.3-2','3.3-3','3.4']);
  assert.ok(catalog.slice(6).every((chapter) => chapter.units.length === 0));
});
test('a single Part can be released without adjacent Parts', () => {
  assert.deepEqual(validateReleases(['3.3-1']), ['3.3-1']);
});
test('unknown, duplicate, sample and path traversal release IDs fail closed', () => {
  for (const input of [['3.3-4'], ['1.1','1.1'], ['layout-preview'], ['../draft'], ['3.3'], null]) {
    assert.throws(() => validateReleases(input));
  }
});
test('production contains exactly the release list; the sample is explicitly opt-in', () => {
  assert.deepEqual(availableDocuments(false).map((document) => document.id), releaseIds);
  assert.ok(availableDocuments(false).every((document) => !document.sample));
  assert.deepEqual(availableDocuments(true).filter((document) => !document.id.startsWith('local-review-')).map((document) => document.id), [...releaseIds, 'layout-preview']);
});
test('samples and ambiguous block identities cannot become published content', () => {
  const sample = loadSample();
  assert.throws(() => validateChecklist(sample, sample.id));
  sample.sections[1].blocks[0].id = sample.sections[0].blocks[0].id;
  assert.throws(() => validateChecklist(sample, sample.id, true), /unique/);
});
test('knowledge tables and worked examples fail validation when incomplete', () => {
  const sample = loadSample();
  const table = sample.sections[0].blocks.find((block) => block.type === 'comparison');
  table.rows[0].pop();
  assert.throws(() => validateChecklist(sample, sample.id, true), /column headings/);
  const second = loadSample();
  second.sections[1].blocks.find((block) => block.type === 'example').result = '';
  assert.throws(() => validateChecklist(second, second.id, true), /problem, steps and result/);
});

test('answer-point prompts require non-empty text entries', () => {
  const sample = loadSample();
  const answer = sample.sections[0].blocks.find((block) => block.type === 'answer-points');
  assert.ok(answer);
  assert.doesNotThrow(() => validateChecklist(sample, sample.id, true));
  answer.items = ['A complete answer point.', ''];
  assert.throws(() => validateChecklist(sample, sample.id, true), /non-empty text/);
  answer.items = [];
  assert.throws(() => validateChecklist(sample, sample.id, true), /non-empty text/);
});

test('calculation inputs and explicit PDF page groups are checked before rendering', () => {
  const fixture = () => {
    const data = loadSample();
    data.sections = [{id:'calculation-fixture',title:'Calculation fixture',blocks:[
      {id:'divide',type:'division',title:'Division',value:173,base:2,printPage:1},
      {id:'bits',type:'bit-grid',title:'Bits',width:8,rows:[{label:'Value',bits:'00101101'}],printPage:1},
      {id:'add',type:'binary-addition',title:'Addition',a:45,b:39,width:8,explanation:'Carry to the next column.',printPage:2},
      {id:'shift',type:'logical-shift',title:'Shift',value:13,direction:'right',places:2,width:8,explanation:'Discard the two low bits.',printPage:2},
    ]}];
    data.pdfPageTitles = ['First page', 'Second page'];
    return data;
  };
  assert.doesNotThrow(() => validateChecklist(fixture(), 'layout-preview', true));
  for (const mutate of [
    (d) => d.sections[0].blocks[0].value = 65536,
    (d) => d.sections[0].blocks[1].rows[0].bits = '101',
    (d) => d.sections[0].blocks[1].weights = [1,2],
    (d) => d.sections[0].blocks[2].a = 256,
    (d) => d.sections[0].blocks[3].places = 9,
    (d) => d.sections[0].blocks[0].printPage = 2,
    (d) => d.sections[0].blocks[3].printPage = 1,
    (d) => d.pdfPageTitles.push('Empty page'),
  ]) {
    const invalid = fixture(); mutate(invalid);
    assert.throws(() => validateChecklist(invalid, 'layout-preview', true));
  }
});

function reviewFixture(t) {
  const directory = mkdtempSync(path.join(tmpdir(), 'checklist-local-review-'));
  t.after(() => rmSync(directory, { recursive: true, force: true }));
  mkdirSync(path.join(directory, 'content/samples'), { recursive: true });
  mkdirSync(path.join(directory, 'drafts'));
  const write = (file, value) => writeFileSync(path.join(directory, file), JSON.stringify(value));
  write('content/catalog.json', catalog);
  write('content/releases.json', { published: [] });
  write('content/samples/layout-preview.json', loadSample());
  const draft = { ...loadSample(), id: '1.1', label: '1.1', sample: false };
  write('drafts/1.1.json', draft);
  const run = (selector, preview) => {
    const env = { ...process.env, CHECKLIST_ROOT: directory, CHECKLIST_REVIEW_ID: selector };
    return spawnSync(process.execPath, ['--input-type=module', '--eval', `
      import { availableDocuments } from ${JSON.stringify(new URL('../lib/content.mjs', import.meta.url).href)};
      console.log(JSON.stringify(availableDocuments(${preview})));
    `], { env, encoding: 'utf8' });
  };
  return { directory, draft, write, run };
}

test('selected draft gets a separate marked local document without opening its chapter', (t) => {
  const fixture = reviewFixture(t);
  const result = fixture.run('1.1', true);
  assert.equal(result.status, 0, result.stderr);
  const documents = JSON.parse(result.stdout);
  assert.deepEqual(documents.map((document) => document.id), ['layout-preview', 'local-review-1.1']);
  const review = documents[1];
  assert.equal(review.sample, true);
  assert.equal(review.label, '1.1');
  assert.deepEqual(review.sections, fixture.draft.sections);
  assert.deepEqual(JSON.parse(readFileSync(path.join(fixture.directory, 'drafts/1.1.json'), 'utf8')), fixture.draft);
  assert.deepEqual(JSON.parse(readFileSync(path.join(fixture.directory, 'content/releases.json'), 'utf8')), { published: [] });
});

test('local review rejects unknown and path-like selectors before opening a draft', (t) => {
  const fixture = reviewFixture(t);
  for (const selector of ['../outside', 'layout-preview', '3.3', '1.1/../../outside']) {
    const result = fixture.run(selector, true);
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /Unknown release ID/);
  }
  const missing = fixture.run('3.3-2', true);
  assert.notEqual(missing.status, 0);
  assert.match(missing.stderr, /ENOENT/);
  fixture.write('drafts/1.1.json', { ...fixture.draft, id: '1.2' });
  const mismatched = fixture.run('1.1', true);
  assert.notEqual(mismatched.status, 0);
  assert.match(mismatched.stderr, /content ID does not match/);
});

test('production ignores a malformed selector, missing draft and malformed draft contents', (t) => {
  const fixture = reviewFixture(t);
  writeFileSync(path.join(fixture.directory, 'drafts/1.1.json'), '{not json');
  for (const selector of ['../outside', '3.3-2', '1.1']) {
    const result = fixture.run(selector, false);
    assert.equal(result.status, 0, result.stderr);
    assert.deepEqual(JSON.parse(result.stdout), []);
  }
});
