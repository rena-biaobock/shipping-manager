const { test, describe } = require('node:test');
const assert = require('node:assert/strict');
const { ffd } = require('../src/ffd');

const label = (progressivo, volume_tons, piece_count = 10) => ({
  progressivo, volume_tons, piece_count,
  item_code: 'TEST', description: `item-${progressivo}`, customer: 'ACME', status: 'reserved',
});

describe('ffd', () => {
  test('packs items into bins within capacity', () => {
    const bins = ffd([label('A', 10), label('B', 8), label('C', 7), label('D', 3)], 15);
    assert.ok(bins.length >= 2);
    for (const bin of bins) {
      assert.ok(bin.totalTons <= 15, `bin exceeds capacity: ${bin.totalTons}`);
    }
  });

  test('all items fit when sum equals capacity exactly', () => {
    const bins = ffd([label('A', 10), label('B', 5)], 15);
    assert.equal(bins.length, 1);
    assert.equal(bins[0].totalTons, 15);
  });

  test('excludes items that individually exceed truck capacity', () => {
    const bins = ffd([label('A', 50), label('B', 5)], 10);
    assert.equal(bins.length, 1);
    assert.equal(bins[0].items[0].progressivo, 'B');
  });

  test('returns empty array for empty input', () => {
    assert.deepEqual(ffd([], 27), []);
  });

  test('returns empty array when all items exceed capacity', () => {
    assert.deepEqual(ffd([label('A', 100), label('B', 200)], 27), []);
  });

  test('respects maxIterations cap', () => {
    const labels = Array.from({ length: 100 }, (_, i) => label(String(i), 1));
    const bins   = ffd(labels, 27, 10);
    const total  = bins.reduce((s, b) => s + b.items.length, 0);
    assert.ok(total <= 10, `Expected ≤10 items processed, got ${total}`);
  });

  test('assigns a unique _id to each bin', () => {
    const labels = Array.from({ length: 5 }, (_, i) => label(String(i), 10));
    const ids    = ffd(labels, 10).map(b => b._id);
    assert.equal(new Set(ids).size, ids.length, 'Duplicate _id detected');
  });

  test('accumulates totalPcs correctly', () => {
    const bins = ffd([label('A', 5, 20), label('B', 5, 30)], 15);
    assert.equal(bins.length, 1);
    assert.equal(bins[0].totalPcs, 50);
  });

  test('sorts descending — large items placed first', () => {
    const bins = ffd([label('small', 1), label('big', 9)], 10);
    assert.equal(bins.length, 1);
    assert.equal(bins[0].items[0].progressivo, 'big');
  });
});
