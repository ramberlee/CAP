import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { BlockAnimation } from '../../types';

/**
 * Resolve a BlockAnimation spec into current-frame opacity/transform values.
 * Used by every block component for consistent entry animation timing.
 */
export function useBlockEntry(
  animation: BlockAnimation | undefined,
  staggerOffset = 0,
  sceneDurationInFrames?: number,
) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const type = animation?.type ?? 'fade';
  const delay = (animation?.delay ?? 0) + staggerOffset;
  const duration = animation?.duration ?? 0.4;

  const t = Math.max(0, frame / fps - delay);
  const progress = Math.min(t / duration, 1);
  const easeOut = 1 - Math.pow(1 - progress, 3);

  let opacity = easeOut;
  let transform = 'none';
  switch (type) {
    case 'fade':
      opacity = easeOut;
      break;
    case 'slideUp':
      opacity = easeOut;
      transform = `translateY(${interpolate(easeOut, [0, 1], [24, 0])}px)`;
      break;
    case 'slideRight':
      opacity = easeOut;
      transform = `translateX(${interpolate(easeOut, [0, 1], [-24, 0])}px)`;
      break;
    case 'scaleIn':
      opacity = easeOut;
      transform = `scale(${interpolate(easeOut, [0, 1], [0.92, 1])})`;
      break;
    case 'typewriter':
      opacity = 1;
      break;
    case 'none':
    default:
      opacity = 1;
      break;
  }

  // Optional scene-end fade (last 10 frames), only when sceneDurationInFrames provided.
  if (sceneDurationInFrames) {
    const fadeOutStart = Math.max(0, sceneDurationInFrames - 10);
    const fadeOut = interpolate(frame, [fadeOutStart, sceneDurationInFrames], [1, 0], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
    opacity = opacity * fadeOut;
  }

  return { opacity, transform, frame, fps };
}
