import { useCurrentFrame } from 'remotion';

/**
 * Cubic ease-out curve for smooth animations.
 * Same as used in v2 layouts: 1 - (1 - progress)³
 */
function cubicEaseOut(t: number): number {
  return 1 - Math.pow(1 - Math.max(0, Math.min(1, t)), 3);
}

export interface StaggeredAnimationOptions {
  itemCount: number;
  staggerDelay?: number;  // frames between items
  entryDuration?: number; // frames per item animation
  startFrame?: number;    // offset start frame
}

export interface StaggeredItemState {
  opacity: number;
  transformY: number;
  progress: number;
  visible: boolean;
}

/**
 * Hook for staggered entry animations.
 * Returns animation values for each item in a list.
 */
export function useStaggeredAnimation({
  itemCount,
  staggerDelay = 4,
  entryDuration = 12,
  startFrame = 0,
}: StaggeredAnimationOptions): StaggeredItemState[] {
  const frame = useCurrentFrame();

  return Array.from({ length: itemCount }, (_, i) => {
    const itemStartFrame = startFrame + i * staggerDelay;
    const elapsed = frame - itemStartFrame;
    const progress = cubicEaseOut(elapsed / entryDuration);

    return {
      progress,
      opacity: progress,
      transformY: (1 - progress) * 20, // slide up 20px
      visible: elapsed >= 0,
    };
  });
}

/**
 * Simplified version for a single item with delay.
 */
export function useDelayedAnimation({
  delay = 0,
  duration = 12,
}: {
  delay?: number;
  duration?: number;
}): StaggeredItemState {
  const frame = useCurrentFrame();
  const elapsed = frame - delay;
  const progress = cubicEaseOut(elapsed / duration);

  return {
    progress,
    opacity: progress,
    transformY: (1 - progress) * 20,
    visible: elapsed >= 0,
  };
}
