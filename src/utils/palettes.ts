export interface Palette {
  name: string;
  bg: string;
  particles: string[];
  accent: string;
  glow: string;
}

export const PALETTES: Record<string, Palette> = {
  phantom: {
    name: "Phantom",
    bg: "#06060A",
    particles: ["#FFFFFF", "#C8C8D0", "#8888AA", "#555577", "#AAAACC"],
    accent: "#8B5CF6",
    glow: "#7C3AED",
  },
  neon_noir: {
    name: "Neon Noir",
    bg: "#050508",
    particles: ["#E0E0E8", "#A0A0B8", "#FF2D55", "#FF6B8A", "#C0C0D0"],
    accent: "#FF2D55",
    glow: "#FF0A3E",
  },
  cold_steel: {
    name: "Cold Steel",
    bg: "#08080C",
    particles: ["#D4D4E0", "#9898B0", "#6E6E8A", "#B0B0C8", "#FFFFFF"],
    accent: "#00F0FF",
    glow: "#00C8D7",
  },
  ember: {
    name: "Ember",
    bg: "#0A0806",
    particles: ["#F5E6D0", "#D4A574", "#FF8C42", "#FFFFFF", "#C09060"],
    accent: "#FF6B00",
    glow: "#FF4500",
  },
};

export const getPalette = (name: string): Palette => {
  return PALETTES[name] || PALETTES.phantom;
};
