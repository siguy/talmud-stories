import { buildIssue } from "./feedback-worker.js";
import assert from "node:assert";
const ok = { story_id: "ketubot-20a-2-3", tractate: "ketubot", ref: "Ketubot 20a", category: "translation", comment: "line 2 is unclear\n```x```", segment: { ref: "Ketubot 20a", index: 2, he: "א", en: "b" }, name: "Dana" };
const i = buildIssue(ok);
assert(i.title.includes("Ketubot 20a segment 2") && i.labels.includes("tractate:ketubot"));
assert(!i.body.split("```json")[1].split("```")[0].includes("```"));
assert.throws(() => buildIssue({ ...ok, story_id: "x; DROP" })); assert.throws(() => buildIssue({ ...ok, category: "zzz" }));
assert.throws(() => buildIssue({ ...ok, category: "other", comment: " " }));
console.log("worker ok");
