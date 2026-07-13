const BR_TAG = /<br\s*\/?>/gi;
const HTML_TAG = /<[^>]+>/g;

export type PreparedSummary = {
  text: string;
  structured: boolean;
};

/** Turn encoded/inline HTML descriptions into plain text for display. */
export function prepareSummary(raw: string): PreparedSummary {
  const hasBreaks = BR_TAG.test(raw);
  BR_TAG.lastIndex = 0;

  let text = raw.replace(BR_TAG, "\n").replace(HTML_TAG, "");
  text = text.replace(/\n{3,}/g, "\n\n").trim();

  const structured = hasBreaks || text.includes("\n");
  return { text, structured };
}
