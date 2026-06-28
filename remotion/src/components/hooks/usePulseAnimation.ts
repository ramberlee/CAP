import { useCurrentFrame } from 'remotion';

export interface PulseAnimationOptions {
  frequency?: number;     // cycles per second (at 30fps)
  intensity?: number;     // 0-1, how strong the pulse is
  phase?: number;         // offset phase (0-1)
  minOpacity?: number;    // minimum opacity
  maxOpacity?: number;    // maximum opacity
}

export interface PulseAnimationState {
  opacity: number;
  scale: number;
  glowIntensity: number;
  borderBrightness: number;
}

/**
 * Hook for breathing/pulsing animations.
 * Uses sine wave to create smooth, organic pulsing effect.
 */
export function usePulseAnimation({
  frequency = 0.5,
  intensity = 1,
  phase = 0,
  minOpacity = 0.6,
  maxOpacity = 1,
}: PulseAnimationOptions = {}): PulseAnimationState {
  const frame = useCurrentFrame();

  // Convert frequency from Hz to radians per frame (at 30fps)
  const radiansPerFrame = (frequency * 2 * Math.PI) / 30;
  const phaseOffset = phase * 2 * Math.PI;
  const sineValue = Math.sin(frame * radiansPerFrame + phaseOffset);

  // Normalize sine to 0-1 range
  const normalized = (sineValue + 1) / 2;

  // Apply intensity and map to desired range
  const pulseValue = minOpacity + normalized * (maxOpacity - minOpacity) * intensity;

  return {
    opacity: pulseValue,
    scale: 1 + (pulseValue - minOpacity) * 0.02, // subtle scale effect
    glowIntensity: (pulseValue - minOpacity) / (maxOpacity - minOpacity) * intensity,
    borderBrightness: 0.3 + pulseValue * 0.7,
  };
}

/**
 * Hook for one-shot pulse on entry (peak then decay).
 * Useful for highlighting new elements.
 */
export function useEntryPulse({
  startFrame = 0,
  peakFrame = 8,
  decayFrames = 20,
}: {
  startFrame?: number;
  peakFrame?: number;
  decayFrames?: number;
}): PulseAnimationState {
  const frame = useCurrentFrame();
  const elapsed = frame - startFrame;

  if (elapsed <= 0) {
    return { opacity: 0, scale: 1, glowIntensity: 0, borderBrightness: 0.3 };
  }

  // Rise to peak, then decay
  const progress = elapsed <= peakFrame
    ? elapsed / peakFrame
    : 1 - (elapsed - peakFrame) / decayFrames;

  const clampedProgress = Math.max(0, Math.min(1, progress));
  const eased = 1 - Math.pow(1 - clampedProgress, 2);

  return {
    opacity: 0.4 + eased * 0.6,
    scale: 1 + eased * 0.05,
    glowIntensity: eased,
    borderBrightness: 0.3 + eased * 0.7,
  };
}
