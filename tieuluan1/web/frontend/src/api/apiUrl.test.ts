import assert from "node:assert/strict";
import test from "node:test";

import { normaliseApiBaseUrl } from "./predictionApi.ts";


test("normaliseApiBaseUrl keeps explicit http protocols", () => {
  assert.equal(
    normaliseApiBaseUrl("http://127.0.0.1:5000/"),
    "http://127.0.0.1:5000",
  );
});


test("normaliseApiBaseUrl converts a Render hostname to https", () => {
  assert.equal(
    normaliseApiBaseUrl("ai-term-paper-api.onrender.com"),
    "https://ai-term-paper-api.onrender.com",
  );
});


test("normaliseApiBaseUrl uses the local API when unset", () => {
  assert.equal(normaliseApiBaseUrl(""), "http://127.0.0.1:5000");
});
