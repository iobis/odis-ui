export type TypeThemeKey = "dataset" | "literature" | "org" | "training" | "project" | "default";

export interface TypeTheme {
  key: TypeThemeKey;
  badge: string;
}

const TYPE_THEMES: Record<string, TypeTheme> = {
  dataset: { key: "dataset", badge: "dataset" },
  creativework: { key: "literature", badge: "literature" },
  person: { key: "org", badge: "person" },
  organization: { key: "org", badge: "organization" },
  event: { key: "training", badge: "event" },
  researchproject: { key: "project", badge: "project" },
  boattrip: { key: "training", badge: "boat trip" },
  service: { key: "default", badge: "service" },
};

function normalizeType(type: string): string {
  return type.toLowerCase().replace(/[\s_-]+/g, "");
}

export function resolveTypeTheme(type: string): TypeTheme {
  const theme = TYPE_THEMES[normalizeType(type)];
  if (theme) return theme;
  return { key: "default", badge: type.toLowerCase() };
}
