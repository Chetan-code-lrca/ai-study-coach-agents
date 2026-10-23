function normalizeFileName(value) {
  return String(value || "")
    .replace(/\\/g, "/")
    .split("/")
    .pop()
    .trim()
    .replace(/\s+/g, " ")
    .toLocaleLowerCase();
}

function normalizeText(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

function hashText(value) {
  // Small deterministic hash is used only to compare local note identities.
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(16);
}

export function noteIdentityKey(note) {
  const sourceFiles = [...new Set(
    (Array.isArray(note?.sourceFiles) ? note.sourceFiles : [])
      .map(normalizeFileName)
      .filter(Boolean),
  )].sort();
  if (sourceFiles.length) return "file:" + sourceFiles.join("|");

  const title = String(note?.title || "Study notes").trim().toLocaleLowerCase();
  const material = normalizeText(note?.material);
  return "text:" + title + ":" + hashText(material);
}

function timestamp(value) {
  const parsed = Date.parse(value || "");
  return Number.isFinite(parsed) ? parsed : 0;
}

function mergeDuplicate(kept, incoming) {
  const keptTime = timestamp(kept.createdAt);
  const incomingTime = timestamp(incoming.createdAt);
  const incomingIsNewer = incomingTime >= keptTime;
  const keptMaterialIsComplete = typeof kept.material === "string" && kept.material.length > 0 && !kept.materialTruncated;
  const incomingMaterialIsComplete = typeof incoming.material === "string" && incoming.material.length > 0 && !incoming.materialTruncated;
  const useIncomingMaterial = incomingMaterialIsComplete && (!keptMaterialIsComplete || incomingIsNewer);
  const merged = {
    ...kept,
    ...(incomingIsNewer ? incoming : {}),
    id: kept.id || incoming.id,
    title: (incomingIsNewer ? incoming.title : kept.title) || kept.title || incoming.title || "Study notes",
    sourceFiles: [...new Set([
      ...(Array.isArray(kept.sourceFiles) ? kept.sourceFiles : []),
      ...(Array.isArray(incoming.sourceFiles) ? incoming.sourceFiles : []),
    ])],
    createdAt: incomingIsNewer ? (incoming.createdAt || kept.createdAt) : (kept.createdAt || incoming.createdAt),
  };

  if (useIncomingMaterial) {
    merged.material = incoming.material;
    merged.materialTruncated = false;
  } else if (keptMaterialIsComplete) {
    merged.material = kept.material;
    merged.materialTruncated = false;
  } else if (typeof incoming.material === "string" && incoming.material.length) {
    merged.material = incoming.material;
    merged.materialTruncated = Boolean(incoming.materialTruncated);
  }

  const materialLength = Math.max(
    Number.isFinite(kept.characters) ? kept.characters : 0,
    Number.isFinite(incoming.characters) ? incoming.characters : 0,
    typeof merged.material === "string" ? merged.material.length : 0,
  );
  if (materialLength) merged.characters = materialLength;
  return merged;
}

/**
 * Collapses repeated imports into a single note per source-file set. The first
 * note ID is retained so existing plans and quiz attempts can be remapped.
 */
export function deduplicateNotesHistory(input) {
  const notes = [];
  const byKey = new Map();
  const idMap = new Map();
  let changed = false;

  for (const original of Array.isArray(input) ? input : []) {
    if (!original || typeof original !== "object") continue;
    const note = { ...original };
    const key = noteIdentityKey(note);
    const existing = byKey.get(key);

    if (!existing) {
      byKey.set(key, note);
      notes.push(note);
      if (note.id) idMap.set(note.id, note.id);
      continue;
    }

    changed = true;
    const merged = mergeDuplicate(existing, note);
    Object.assign(existing, merged);
    if (note.id) idMap.set(note.id, existing.id || note.id);
    if (existing.id) idMap.set(existing.id, existing.id);
  }

  if (notes.length !== (Array.isArray(input) ? input.length : 0)) changed = true;
  return { notes, idMap, changed };
}
