/**
 * Keep useful metadata for the recent-history dashboard while bounding the
 * amount of full text and quiz detail stored in a single Anna Storage value.
 */
export function prepareHistoryForStorage(items, kind, maxItems, detailLimit = 6) {
  if (!Array.isArray(items)) return [];
  const recent = items.slice(-maxItems);
  const keepFrom = Math.max(0, recent.length - detailLimit);
  return recent.map((item, index) => {
    const record = { ...item };
    const keepDetails = index >= keepFrom;
    if (kind === "plan") {
      if (!keepDetails) {
        delete record.planText;
        delete record.planTextTruncated;
      } else if (typeof record.planText === "string" && record.planText.length > 14000) {
        record.planText = record.planText.slice(0, 14000);
        record.planTextTruncated = true;
      }
    } else if (kind === "quiz" && !keepDetails) {
      delete record.questions;
      delete record.answers;
    } else if (kind === "note") {
      if (!keepDetails) {
        delete record.material;
        delete record.materialTruncated;
      } else if (typeof record.material === "string" && record.material.length > 10000) {
        record.material = record.material.slice(0, 10000);
        record.materialTruncated = true;
      }
    }
    return record;
  });
}
