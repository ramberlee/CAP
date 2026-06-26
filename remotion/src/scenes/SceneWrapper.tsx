import React, { useMemo } from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { ThemePalette } from '../themes';
import { MediaBackground, GeometricBackground } from '../components/MediaBackground';
import { Scene } from '../types';

interface SceneWrapperProps {
  scene: Scene;
  theme: ThemePalette;
  children: React.ReactNode;
  /** Override background image */
  backgroundImage?: string;
  /** Ken Burns effect for background */
  kenBurns?: 'zoomIn' | 'zoomOut' | 'none';
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
 * Shared wrapper for all scene components.
 * Handles: background (image/gradient), overlays, content positioning, entrance animation.
 */
export const SceneWrapper: React.FC<SceneWrapperProps> = ({
  scene,
  theme,
  children,
  backgroundImage,
  kenBurns = 'zoomIn',
  overlayOpacity = 0.5,
  blur = 0,
  verticalAlign = 'center',
  horizontalAlign = 'center',
  padding = 80,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // Fade in at start
  const opacity = interpolate(
    frame,
    [0, 15],
    [0, 1],
    { extrapolateRight: 'clamp' }
  );

  // Fade out near end
  const fadeOutStart = Math.max(0, durationInFrames - 10);
  const finalOpacity = interpolate(
    frame,
    [fadeOutStart, durationInFrames],
    [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const alignStyle: React.CSSProperties = useMemo(() => ({
    justifyContent:
      verticalAlign === 'top' ? 'flex-start'
      : verticalAlign === 'bottom' ? 'flex-end'
      : 'center',
    alignItems:
      horizontalAlign === 'left' ? 'flex-start'
      : horizontalAlign === 'right' ? 'flex-end'
      : 'center',
    padding: typeof padding === 'number' ? `${padding}px` : padding,
  }), [verticalAlign, horizontalAlign, padding]);

  const hasImage = !!(backgroundImage || scene.imageUrl);

  return (
    <AbsoluteFill style={{ opacity: finalOpacity }}>
      {/* Background layer */}
      {hasImage ? (
        <MediaBackground
          imageUrl={backgroundImage || scene.imageUrl}
          theme={theme}
          kenBurns={kenBurns}
          overlayOpacity={overlayOpacity}
          blur={blur}
        />
      ) : (
        <GeometricBackground theme={theme} />
      )}

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
