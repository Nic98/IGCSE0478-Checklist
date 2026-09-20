import test from 'node:test';
import assert from 'node:assert/strict';
import { samplingPanels, validateSamplingDiagram } from '../lib/sampling.mjs';

const diagram = () => ({
  duration: 1,
  waveform: [0, 0.7, 1, 0.35, 0],
  panels: [
    { label: 'A', sampleRate: 4, resolution: 2 },
    { label: 'B', sampleRate: 8, resolution: 2 },
    { label: 'C', sampleRate: 4, resolution: 3 },
  ],
});

test('sampling excludes the final endpoint and preserves times when only resolution changes', () => {
  const [a, b, c] = samplingPanels(diagram());
  assert.deepEqual(a.samples.map((sample) => sample.time), [0, 0.25, 0.5, 0.75]);
  assert.equal(b.samples.length, 8);
  assert.equal(b.samples.at(-1).time, 0.875);
  assert.deepEqual(c.samples.map((sample) => sample.time), a.samples.map((sample) => sample.time));
  assert.equal(b.samples[1].amplitude, 0.35);
});

test('stored values use the available levels with bounded quantization error', () => {
  const [a, , c] = samplingPanels(diagram());
  assert.equal(a.levels.length, 4);
  assert.equal(c.levels.length, 8);
  for (const panel of [a, c]) {
    assert.equal(panel.levels[0], 0);
    assert.equal(panel.levels.at(-1), 1);
    for (const sample of panel.samples) {
      assert.ok(panel.levels.includes(sample.stored));
      assert.ok(Math.abs(sample.amplitude - sample.stored) <= 0.5 / (panel.levels.length - 1));
    }
  }
  assert.equal(a.samples[1].stored, 2 / 3);
  assert.equal(c.samples[1].stored, 5 / 7);
  assert.ok(Math.abs(c.samples[1].amplitude - c.samples[1].stored) < Math.abs(a.samples[1].amplitude - a.samples[1].stored));
});

test('sampling rejects unbounded or invalid diagram inputs', () => {
  for (const duration of [0, -1, Infinity, NaN]) assert.throws(() => validateSamplingDiagram({ ...diagram(), duration }));
  for (const waveform of [[], [0], [-0.1, 1], [0, 1.1], [0, NaN]]) assert.throws(() => validateSamplingDiagram({ ...diagram(), waveform }));
  for (const panels of [[], Array(4).fill(diagram().panels[0])]) assert.throws(() => validateSamplingDiagram({ ...diagram(), panels }));
  for (const sampleRate of [0, 1.5, 33, Infinity]) assert.throws(() => validateSamplingDiagram({ ...diagram(), panels: [{ ...diagram().panels[0], sampleRate }] }));
  for (const resolution of [0, 1.5, 5]) assert.throws(() => validateSamplingDiagram({ ...diagram(), panels: [{ ...diagram().panels[0], resolution }] }));
  assert.throws(() => validateSamplingDiagram({ ...diagram(), duration: 5 }));
  assert.throws(() => validateSamplingDiagram({ ...diagram(), panels: [{ ...diagram().panels[0], label: '' }] }));
});
