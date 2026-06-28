import { useCurrentFrame, useVideoConfig } from 'remotion';

export interface FlowAnimationOptions {
  pathLength?: number;     // total length of the path in pixels
  speed?: number;          // pixels per frame
  dotCount?: number;       // number of flowing dots
  dotSpacing?: number;     // spacing between dots in pixels
  loop?: boolean;          // whether animation loops
}

export interface FlowDotState {
  position: number;        // current position along path (0-1)
  opacity: number;         // fade in/out at edges
  visible: boolean;
}

export interface FlowAnimationState {
  dots: FlowDotState[];
  dashOffset: number;      // for dashed line animation
  progress: number;        // overall animation progress (0-1)
}

/**
 * Hook for flowing dots along a path.
 * Used in ConnectorLine component for "data flowing" effect.
 */
export function useFlowAnimation({
  pathLength = 500,
  speed = 3,
  dotCount = 3,
  dotSpacing = 150,
  loop = true,
}: FlowAnimationOptions = {}): FlowAnimationState {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Calculate total offset (pixels traveled)
  const totalOffset = frame * speed;

  // For dashed line animation
  const dashOffset = -totalOffset;

  // Calculate individual dot positions
  const dots: FlowDotState[] = Array.from({ length: dotCount }, (_, i) => {
    const dotStart = i * dotSpacing;
    const pixelPosition = (totalOffset + dotStart) % pathLength;
    const position = pixelPosition / pathLength;

    // Fade in at start, fade out at end (for non-looping)
    const fadeZone = 0.15;
    let opacity = 1;
    if (!loop) {
      if (position < fadeZone) {
        opacity = position / fadeZone;
      } else if (position > 1 - fadeZone) {
        opacity = (1 - position) / fadeZone;
      }
    }

    // For looping, fade in from start, fade out near end
    if (loop) {
      if (position < fadeZone) {
        opacity = position / fadeZone;
      } else if (position > 1 - fadeZone) {
        opacity = (1 - position) / fadeZone;
      }
    }

    return {
      position,
      opacity,
      visible: opacity > 0.01,
    };
  });

  // Overall progress (for non-looping animations)
  const progress = loop
    ? (totalOffset % pathLength) / pathLength
    : Math.min(1, totalOffset / pathLength);

  return {
    dots,
    dashOffset,
    progress,
  };
}

/**
 * Simple version for a single dot moving from start to end.
 */
export function useSingleDotFlow({
  duration = 60,  // frames for complete traversal
  startFrame = 0,
}: {
  duration?: number;
  startFrame?: number;
} = {}): { position: number; opacity: number } {
  const frame = useCurrentFrame();
  const elapsed = Math.max(0, frame - startFrame);
  const progress = Math.min(1, elapsed / duration);

  // Ease in-out
  const eased = progress < 0.5
    ? 2 * progress * progress
    : 1 - Math.pow(-2 * progress + 2, 2) / 2;

  // Fade in at start, fade out at end
  const fadeIn = Math.min(1, elapsed / 10);
  const fadeOut = elapsed > duration - 10
    ? (duration - elapsed) / 10
    : 1;

  return {
    position: eased,
    opacity: fadeIn * fadeOut,
  };
}
