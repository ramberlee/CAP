import React, { useMemo } from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { ThemePalette } from '../themes';
import { Scene } from '../types';
import { isDarkGlassTheme } from '../themes';

interface SceneWrapperProps {
  scene: Scene;
  theme: ThemePalette;
  children: React.ReactNode;
  /** Override background image */
  backgroundImage?: string;
  /** Overlay opacity */
  overlayOpacity?: number;
  /** Whether image should be blurred */
  blur?: number;
  /** Vertical alignment of content */
  verticalAlign?: 'top' | 'center' | 'bottom';
  /** Horizontal alignment of content */
  horizontalAlign?: 'left' | 'center' | 'right';
  /** Padding in px */
  padding?: number | string;
}

/**
 * Shared wrapper for legacy (v1) scene components.
 * Clean PPT-style: simple background, content layer, fade in/out.
 *
 * Applies glass background variants when the active theme is `dark_glass`.
 */
export const SceneWrapper: React.FC<SceneWrapperProps> = ({
  scene,
  theme,
  children,
  backgroundImage,
  overlayOpacity = 0.5,
  blur = 0,
  verticalAlign = 'center',
  horizontalAlign = 'center',
  padding = 80,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // Fade in at start
  const opacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: 'clamp' });

  // Fade out near end
  const fadeOutStart = Math.max(0, durationInFrames - 10);
  const finalOpacity = interpolate(
    frame,
    [fadeOutStart, durationInFrames],
    [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' },
  );

  const alignStyle: React.CSSProperties = useMemo(
    () => ({
      justifyContent:
        verticalAlign === 'top' ? 'flex-start'
        : verticalAlign === 'bottom' ? 'flex-end'
        : 'center',
      alignItems:
        horizontalAlign === 'left' ? 'flex-start'
        : horizontalAlign === 'right' ? 'flex-end'
        : 'center',
      padding: typeof padding === 'number' ? `${padding}px` : padding,
    }),
    [verticalAlign, horizontalAlign, padding],
  );

  const hasImage = !!(backgroundImage || scene.imageUrl);
  const useGlass = isDarkGlassTheme(theme);

  return (
    <AbsoluteFill style={{ opacity: finalOpacity }}>
      {/* Background */}
      <AbsoluteFill
        style={{
          background: hasImage
            ? undefined
            : (theme.backgroundGradient || theme.background),
        }}
      >
        {hasImage && (
          <>
            <AbsoluteFill>
              <img
                src={backgroundImage || scene.imageUrl!}
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover',
                  filter: blur > 0 ? `blur(${blur}px)` : undefined,
                }}
              />
            </AbsoluteFill>
            {/* Simple dark overlay for readability */}
            <AbsoluteFill
              style={{
                background: `rgba(0,0,0,${overlayOpacity})`,
              }}
            />
          </>
        )}

        {/* Subtle dot grid for dark_glass theme (no children — pure background) */}
        {useGlass && !hasImage && (
          <AbsoluteFill
            style={{
              backgroundImage: `radial-gradient(${
                theme.dotGridColor ?? 'rgba(255,255,255,0.05)'
              } 1.2px, transparent 1.7px)`,
              backgroundSize: '48px 48px',
              pointerEvents: 'none',
            }}
          />
        )}
      </AbsoluteFill>

      {/* Content layer */}
      <AbsoluteFill
        style={{
          display: 'flex',
          flexDirection: 'column',
          ...alignStyle,
          zIndex: 1,
          opacity,
        }}
      >
        {children}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
