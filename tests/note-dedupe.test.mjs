import assert from "node:assert/strict";
import test from "node:test";
import { deduplicateNotesHistory, noteIdentityKey } from "../anna-app/src/note-dedupe.js";

test("repeat imports of the same file collapse to one note and preserve link IDs", () => {
  const notes = [
    {
      id: "note-old",
      title: "Machine Learning Notes",
      sourceFiles: ["CSE2507_ML_Notes.pdf"],
      material: "Old preview text",
      materialTruncated: true,
      characters: 28458,
      createdAt: "2026-10-21T10:00:00.000Z",
    },
    {
      id: "note-new",
      title: "Machine Learning Notes",
      sourceFiles: ["cse2507_ml_notes.PDF"],
      material: "Complete extracted Machine Learning notes, including every section.",
      materialTruncated: false,
      characters: 28458,
      createdAt: "2026-10-22T10:00:00.000Z",
    },
  ];

  const result = deduplicateNotesHistory(notes);
  assert.equal(result.notes.length, 1);
  assert.equal(result.notes[0].id, "note-old");
  assert.equal(result.notes[0].material, "Complete extracted Machine Learning notes, including every section.");
  assert.equal(result.notes[0].materialTruncated, false);
  assert.equal(result.notes[0].title, "Machine Learning Notes");
  assert.equal(result.idMap.get("note-old"), "note-old");
  assert.equal(result.idMap.get("note-new"), "note-old");
  assert.equal(result.changed, true);
});

test("different source files remain separate even when their titles match", () => {
  const notes = [
    { id: "a", title: "Lecture notes", sourceFiles: ["lecture-1.pdf"], material: "Topic one" },
    { id: "b", title: "Lecture notes", sourceFiles: ["lecture-2.pdf"], material: "Topic two" },
  ];
  const result = deduplicateNotesHistory(notes);
  assert.equal(result.notes.length, 2);
  assert.notEqual(noteIdentityKey(notes[0]), noteIdentityKey(notes[1]));
});

test("identical pasted material is not duplicated in history", () => {
  const notes = [
    { id: "paste-a", title: "Revision sheet", sourceFiles: [], material: "Definitions and examples for revision." },
    { id: "paste-b", title: " Revision sheet ", sourceFiles: [], material: "Definitions   and examples for revision." },
  ];
  const result = deduplicateNotesHistory(notes);
  assert.equal(result.notes.length, 1);
  assert.equal(result.idMap.get("paste-b"), "paste-a");
});

test("a full saved note is kept when a duplicate is only a truncated preview", () => {
  const notes = [
    { id: "complete", title: "OS Notes", sourceFiles: ["os.pdf"], material: "The complete and longer extracted note text.", characters: 500, createdAt: "2026-10-22T10:00:00.000Z" },
    { id: "preview", title: "OS Notes", sourceFiles: ["os.pdf"], material: "The preview", materialTruncated: true, characters: 500, createdAt: "2026-10-23T10:00:00.000Z" },
  ];
  const result = deduplicateNotesHistory(notes);
  assert.equal(result.notes.length, 1);
  assert.equal(result.notes[0].material, "The complete and longer extracted note text.");
  assert.equal(result.notes[0].materialTruncated, false);
});
