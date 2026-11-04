import assert from "node:assert/strict";
import test from "node:test";

import { formatSequence, parseSequenceText } from "./sequence.ts";


test("parseSequenceText reads comma-separated rows", () => {
  const result = parseSequenceText("1, 2, 3, 4, 5\n6,7,8,9,10", 2);

  assert.deepEqual(result, [
    [1, 2, 3, 4, 5],
    [6, 7, 8, 9, 10],
  ]);
});


test("parseSequenceText rejects the wrong number of rows or columns", () => {
  assert.throws(
    () => parseSequenceText("1,2,3,4,5", 2),
    /đúng 2 hàng/,
  );
  assert.throws(
    () => parseSequenceText("1,2,3\n4,5,6", 2),
    /Hàng 1 phải có đúng 5 số/,
  );
});


test("parseSequenceText rejects non-finite values", () => {
  assert.throws(
    () => parseSequenceText("1,2,3,4,Infinity", 1),
    /Hàng 1 phải có đúng 5 số hữu hạn/,
  );
});


test("formatSequence can be parsed without losing numeric values", () => {
  const sequence = [
    [101.25, 104, 99.5, 102.75, 1200000],
    [102.75, 105, 101, 104.5, 900000],
  ];

  assert.deepEqual(parseSequenceText(formatSequence(sequence), 2), sequence);
});
