export function formatTypeLabel(value: string): string {
  if (value === "creativework") return "Creative Work";
  if (value === "researchproject") return "Research Project";
  if (value === "boattrip") return "Cruise";
  if (value === "course") return "Course";
  return value.charAt(0).toUpperCase() + value.slice(1);
}

export function sourceLabel(id: string, name?: string | null): string {
  return name ? `${name} (${id})` : id;
}
