export function formatMinutes(minutes: number | null | undefined): string | null {
  if (minutes == null) return null;
  if (minutes < 60) return `${minutes} min`;

  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return rest ? `${hours} hr ${rest} min` : `${hours} hr`;
}

export function totalTimeMinutes(r: {
  prep_time: number | null;
  cook_time: number | null;
}): number | null {
  const parts = [r.prep_time, r.cook_time].filter((v): v is number => v != null);
  return parts.length ? parts.reduce((sum, v) => sum + v, 0) : null;
}