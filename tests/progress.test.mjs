import test from 'node:test';
import assert from 'node:assert/strict';
import { readProgress, saveProgress, storageKey } from '../lib/progress.mjs';
const memory = () => { const map = new Map(); return { getItem: (key) => map.get(key) ?? null, setItem: (key, value) => map.set(key, value) }; };

test('stable IDs survive reorder; new and deleted objectives have correct state', () => {
  const storage = memory();
  saveProgress(storage, '1.1', { 'first': 'confident', 'second': 'developing', 'removed': 'not-yet' });
  assert.deepEqual(readProgress(storage, '1.1', ['second','new','first']), { second:'developing', first:'confident' });
});
test('chapters, Parts and samples have independent local storage', () => {
  const storage = memory();
  saveProgress(storage, '3.3-1', { first:'confident' });
  assert.deepEqual(readProgress(storage, '3.3-2', ['first']), {});
  assert.deepEqual(readProgress(storage, 'layout-preview', ['first']), {});
  assert.ok(storageKey('3.3-1').startsWith('igcse0478-checklist:'));
});
test('unexpected stored values are ignored and storage failures reach the UI handler', () => {
  const storage = memory();
  storage.setItem(storageKey('1.1'), JSON.stringify({ one:'invalid', two:'confident' }));
  assert.deepEqual(readProgress(storage, '1.1', ['one','two']), { two:'confident' });
  storage.setItem(storageKey('1.1'), 'broken json');
  assert.throws(() => readProgress(storage, '1.1', ['one']));
  assert.throws(() => saveProgress({ setItem: () => { throw new Error('blocked'); } }, '1.1', {}), /blocked/);
});
