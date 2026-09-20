/**
 * @typedef {{ label: string, sampleRate: number, resolution: number }} SamplingPanel
 * @typedef {{ duration: number, waveform: number[], panels: SamplingPanel[] }} SamplingData
 */

/**
 * Validate the bounded data used by both sampling diagrams and their captions.
 * @param {SamplingData} block
 */
export function validateSamplingDiagram(block) {
  if (!Number.isFinite(block.duration) || block.duration <= 0) {
    throw new Error('sampling diagrams need a positive duration');
  }
  if (!Array.isArray(block.waveform) || block.waveform.length < 2 || block.waveform.some((value) => !Number.isFinite(value) || value < 0 || value > 1)) {
    throw new Error('sampling waveforms need at least two normalized amplitudes between 0 and 1');
  }
  if (!Array.isArray(block.panels) || block.panels.length < 1 || block.panels.length > 3) {
    throw new Error('sampling diagrams need one to three panels');
  }
  for (const panel of block.panels) {
    if (typeof panel.label !== 'string' || !panel.label.trim()) throw new Error('sampling panels need a label');
    if (!Number.isInteger(panel.sampleRate) || panel.sampleRate < 1 || panel.sampleRate > 32) {
      throw new Error('sampling rates must be integers from 1 to 32 Hz');
    }
    if (!Number.isInteger(panel.resolution) || panel.resolution < 1 || panel.resolution > 4) {
      throw new Error('sampling resolution must be 1 to 4 bits');
    }
    if (block.duration * panel.sampleRate > 32) throw new Error('sampling panels may contain at most 32 samples');
  }
  return block;
}

/**
 * Sample the piecewise-linear waveform on [0, duration), then quantize.
 * @param {SamplingData} block
 */
export function samplingPanels(block) {
  validateSamplingDiagram(block);
  return block.panels.map((panel) => {
    const levelCount = 2 ** panel.resolution;
    const samples = [];
    for (let index = 0; index / panel.sampleRate < block.duration; index += 1) {
      const time = index / panel.sampleRate;
      const position = time / block.duration * (block.waveform.length - 1);
      const left = Math.min(Math.floor(position), block.waveform.length - 2);
      const fraction = position - left;
      const amplitude = block.waveform[left] + (block.waveform[left + 1] - block.waveform[left]) * fraction;
      const code = Math.round(amplitude * (levelCount - 1));
      samples.push({ time, amplitude, stored: code / (levelCount - 1), code });
    }
    return {
      ...panel,
      levels: Array.from({ length: levelCount }, (_, index) => index / (levelCount - 1)),
      samples,
    };
  });
}
