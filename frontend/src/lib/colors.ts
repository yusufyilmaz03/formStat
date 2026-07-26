// Grafiklerde tutarlı, erişilebilir kategorik palet
export const PALETTE = [
  "#4f46e5",
  "#059669",
  "#d97706",
  "#dc2626",
  "#0891b2",
  "#7c3aed",
  "#db2777",
  "#65a30d",
  "#2563eb",
  "#ea580c",
];

export const colorAt = (i: number) => PALETTE[i % PALETTE.length];
