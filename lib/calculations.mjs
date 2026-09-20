// Values drive both the labels and the calculation diagrams; no preformatted spaces are required.
const unsigned = (value, width) => {
  if (!Number.isInteger(value) || value < 0 || value >= 2 ** width) throw new RangeError(`Expected an unsigned ${width}-bit integer.`);
};

export function divisionRows(value, base) {
  unsigned(value, 16);
  if (base !== 2 && base !== 16) throw new RangeError('Division base must be 2 or 16.');
  const rows = [];
  do {
    const quotient = Math.floor(value / base);
    rows.push({ dividend: value, quotient, remainder: value % base });
    value = quotient;
  } while (value > 0);
  return rows;
}

export function binaryAddition(a, b, width = 8) {
  if (width !== 8) throw new RangeError('Binary addition uses an 8-bit register.');
  unsigned(a, width);
  unsigned(b, width);
  const carries = Array(width + 1).fill(' ');
  let carry = 0;
  for (let bit = 0; bit < width; bit++) {
    carry = Math.floor((((a >> bit) & 1) + ((b >> bit) & 1) + carry) / 2);
    if (carry) carries[width - bit - 1] = '1';
  }
  const result = a + b;
  return {
    aBits: a.toString(2).padStart(width, '0'), bBits: b.toString(2).padStart(width, '0'),
    sumBits: result.toString(2).padStart(width + 1, '0'), carries: carries.join(''),
    overflow: result >= 2 ** width, result, stored: result % 2 ** width,
  };
}

export function logicalShift(value, direction, places, width = 8) {
  if (width !== 8) throw new RangeError('Logical shifts use an 8-bit register.');
  unsigned(value, width);
  if (!['left', 'right'].includes(direction) || !Number.isInteger(places) || places < 1 || places > width) throw new RangeError('Invalid logical shift.');
  const before = value.toString(2).padStart(width, '0');
  const mathematical = direction === 'left' ? value * 2 ** places : value / 2 ** places;
  const result = direction === 'left' ? mathematical % 2 ** width : Math.floor(mathematical);
  const insertedIndices = Array.from({ length: places }, (_, index) => direction === 'left' ? width - places + index : index);
  return {
    before, after: result.toString(2).padStart(width, '0'),
    lost: direction === 'left' ? before.slice(0, places) : before.slice(width - places),
    insertedIndices, retainedIndices: Array.from({ length: width }, (_, i) => i).filter((i) => !insertedIndices.includes(i)),
    result, mathematical,
  };
}
