import assert from "node:assert/strict";
import test from "node:test";

import { buildAgentPayload, validateAgentQuestion } from "./knowledgeApi.ts";


test("validateAgentQuestion trims repeated whitespace", () => {
  assert.equal(validateAgentQuestion("  What   is diabetes?  "), "What is diabetes?");
});


test("validateAgentQuestion enforces the backend 3-500 character contract", () => {
  assert.throws(() => validateAgentQuestion(" "));
  assert.throws(() => validateAgentQuestion("x".repeat(501)));
});


test("buildAgentPayload exposes only allowlisted fields", () => {
  assert.deepEqual(buildAgentPayload("What is revenue?", "finance"), {
    question: "What is revenue?",
    domain: "finance",
  });
});
