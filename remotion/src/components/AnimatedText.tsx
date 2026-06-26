import React, { useMemo } from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { FONT_FAMILY } from '../styles/typography';

interface AnimatedTextProps {
  text: string;
  /** Animation style */
  animation?: 'fade' | 'slideUp' | 'slideRight' | 'typewriter' | 'scaleIn' | 'none';
  /** Delay in seconds before animation starts */
  delay?: number;
  /** Duration of animation in seconds */
  duration?: number;
  /** Font size in px */
  fontSize?: number;
  /** Font weight */
  fontWeight?: number;
  /** Text color */
  color?: string;
  /** Line height */
  lineHeight?: number;
  /** Letter spacing in px */
  letterSpacing?: number;
  /** Text alignment */
  textAlign?: 'left' | 'center' | 'right';
  /** Opacity (after animation completes) */
  opacity?: number;
  /** Additional style overrides */
  style?: React.CSSProperties;
  /** Class name for container */
  className?: string;
}

/**
 * Animated text component supporting multiple entrance animations.
 * Used by all scene components for consistent text animation.
 */
export const AnimatedText: React.FC<AnimatedTextProps> = ({
  text,
  animation = 'fade',
  delay = 0,
  duration = 0.5,
  fontSize = 28,
  fontWeight = 400,
  color = '#FFFFFF',
  lineHeight = 1.5,
  letterSpacing = 0,
  textAlign = 'left',
  opacity = 1,
  style,
  className,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const t = Math.max(0, frame / fps - delay);

  // For typewriter, we handle opacity/transform in the render branch directly
  const isTypewriter = animation === 'typewriter';

  const { animatedOpacity, transform } = useMemo(() => {
    if (isTypewriter) {
      return { animatedOpacity: 1, transform: 'none' };
    }
    if (animation === 'none' || t < 0) {
      return { animatedOpacity: animation === 'none' ? 1 : 0, transform: 'none' };
    }

    const progress = Math.min(t / duration, 1);
    const easeOut = 1 - Math.pow(1 - progress, 3);

    switch (animation) {
      case 'fade':
        return { animatedOpacity: easeOut, transform: 'none' };

      case 'slideUp':
        return {
          animatedOpacity: easeOut,
          transform: `translateY(${interpolate(easeOut, [0, 1], [40, 0])}px)`,
        };

      case 'slideRight':
        return {
          animatedOpacity: easeOut,
          transform: `translateX(${interpolate(easeOut, [0, 1], [-40, 0])}px)`,
        };

      case 'scaleIn':
        return {
          animatedOpacity: easeOut,
          transform: `scale(${interpolate(easeOut, [0, 1], [0.8, 1])})`,
        };

      default:
        return { animatedOpacity: 1, transform: 'none' };
    }
  }, [t, animation, duration, isTypewriter]);

  if (isTypewriter && t > 0) {
    const charCount = Math.floor(Math.min(t / duration, 1) * text.length);
    return (
      <span
        className={className}
        style={{
          fontSize,
          fontWeight,
          color,
          fontFamily: FONT_FAMILY,
          lineHeight,
          letterSpacing,
          textAlign,
          opacity: t < 0 ? 0 : 1,
          ...style,
        }}
      >
        {text.slice(0, Math.max(0, charCount))}
        {charCount < text.length && (
          <span
            style={{
              opacity: Math.sin(frame * 0.15) > 0 ? 1 : 0,
              fontWeight: 300,
            }}
          >
            |
          </span>
        )}
      </span>
    );
  }

  return (
    <span
      className={className}
      style={{
        fontSize,
        fontWeight,
        color,
        fontFamily: FONT_FAMILY,
        lineHeight,
        letterSpacing,
        textAlign,
        opacity: animatedOpacity * opacity,
        transform,
        ...style,
      }}
    >
      {text}
    </span>
  );
};

/**
 * Typewriter text that types out character by character.
 */
export const TypewriterText: React.FC<{
  text: string;
  fontSize?: number;
  fontWeight?: number;
  color?: string;
  delay?: number;
  speed?: number; // characters per second
}> = ({ text, fontSize = 36, fontWeight = 400, color = '#FFFFFF', delay = 0, speed = 8 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = Math.max(0, (frame / fps) - delay);
  const charCount = Math.min(Math.floor(t * speed), text.length);

  return (
    <span
      style={{
        fontSize,
        fontWeight,
        color,
        fontFamily: FONT_FAMILY,
        lineHeight: 1.5,
      }}
    >
      {text.slice(0, Math.max(0, charCount))}
      {charCount < text.length && (
        <span
          style={{
            opacity: Math.sin(frame * 0.15) > 0 ? 1 : 0,
            fontWeight: 300,
          }}
        >
          |
        </span>
      )}
    </span>
  );
};
