/* Shared color utilities for landscape videos */

export const OVERLAY = 'rgba(0, 0, 0, 0.5)';
export const OVERLAY_LIGHT = 'rgba(0, 0, 0, 0.3)';
export const OVERLAY_HEAVY = 'rgba(0, 0, 0, 0.65)';

export function hexToRgba(hex: string, alpha: number): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}
