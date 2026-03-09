export const lerp = (a: number, b: number, t: number): number => {
  return a + (b - a) * Math.max(0, Math.min(1, t));
};

export const smoothstep = (t: number): number => {
  t = Math.max(0, Math.min(1, t));
  return t * t * (3 - 2 * t);
};

export const easeOutCubic = (t: number): number => {
  return 1 - Math.pow(1 - Math.max(0, Math.min(1, t)), 3);
};

