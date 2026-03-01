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

export const easeInOutQuad = (t: number): number => {
  t = Math.max(0, Math.min(1, t));
  return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
};

export const mapRange = (
  value: number,
  inMin: number,
  inMax: number,
  outMin: number,
  outMax: number,
): number => {
  const t = (value - inMin) / (inMax - inMin);
  return lerp(outMin, outMax, Math.max(0, Math.min(1, t)));
};
