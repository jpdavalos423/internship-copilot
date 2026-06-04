export function formatBreakdownValue(value: string[] | number): string {
  if (Array.isArray(value)) {
    return value.length ? value.join(", ") : "—";
  }

  return String(value);
}
