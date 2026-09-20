import test from 'node:test';
import assert from 'node:assert/strict';
import { divisionRows, binaryAddition, logicalShift } from '../lib/calculations.mjs';

test('division remainders reconstruct the value in the stated base, read from the bottom', () => {
  for (const value of [0, 1, 15, 16, 173, 255, 256, 4660, 65535]) {
    for (const base of [2, 16]) {
      const rows = divisionRows(value, base);
      assert.equal(rows[0].dividend, value);
      assert.equal(rows.at(-1).quotient, 0);
      assert.equal(rows.map((row) => row.remainder.toString(16)).reverse().join(''), value.toString(base));
      rows.forEach((row) => assert.equal(row.dividend, row.quotient * base + row.remainder));
    }
  }
});

test('addition includes consecutive carries, three ones in a column, and the ninth overflow column', () => {
  const example = binaryAddition(45, 39);
  assert.equal(example.sumBits, '001010100');
  assert.equal(example.carries, '  1 1111 ');
  assert.equal(example.overflow, false);
  const overflow = binaryAddition(200, 100);
  assert.equal(overflow.sumBits, '100101100');
  assert.equal(overflow.carries, '11       ');
  assert.equal(overflow.result, 300);
  assert.equal(overflow.stored, 44);
  assert.equal(overflow.overflow, true);
  assert.equal(binaryAddition(255, 255).sumBits, '111111110');
  assert.equal(binaryAddition(100, 50).overflow, false);
});

test('logical shifts show the exact discarded and inserted bits across the full 8-bit range', () => {
  for (let value = 0; value < 256; value++) {
    for (let places = 1; places <= 8; places++) {
      for (const direction of ['left', 'right']) {
        const diagram = logicalShift(value, direction, places);
        const expected = direction === 'left'
          ? diagram.before.slice(places) + '0'.repeat(places)
          : '0'.repeat(places) + diagram.before.slice(0, 8 - places);
        assert.equal(diagram.after, expected);
        assert.equal(diagram.result, parseInt(expected, 2));
        assert.equal(diagram.lost.length, places);
        assert.equal(diagram.insertedIndices.length, places);
        assert.ok(diagram.insertedIndices.every((i) => diagram.after[i] === '0'));
      }
    }
  }
  assert.equal(logicalShift(200, 'left', 1).mathematical, 400);
  assert.equal(logicalShift(200, 'left', 1).result, 144);
  assert.equal(logicalShift(13, 'right', 2).mathematical, 3.25);
  assert.equal(logicalShift(13, 'right', 2).lost, '01');
});

test('calculation diagrams reject values outside their declared scope', () => {
  for (const fn of [() => divisionRows(65536, 2), () => divisionRows(3, 10), () => binaryAddition(-1, 2), () => binaryAddition(256, 0), () => logicalShift(1, 'rotate', 2), () => logicalShift(1, 'left', 0), () => logicalShift(1, 'right', 9)]) assert.throws(fn, RangeError);
});
