import React from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from 'remotion';

export type TransitionType = 'fade' | 'slideLeft' | 'slideRight' | 'slideUp' | 'slideDown' | 'zoomIn' | 'zoomOut' | 'dissolve';

interface TransitionProps {
  /** 过渡类型 */
  type: TransitionType;
  /** 过渡持续帧数 */
  durationInFrames: number;
  /** 是否是出场动画 (默认: false = 入场) */
  isExit?: boolean;
  children: React.ReactNode;
}

/**
 * 通用过渡动画组件
 * 支持多种动画效果，用于场景间切换
 */
export const Transition: React.FC<TransitionProps> = ({
  type = 'fade',
  durationInFrames = 15,
  isExit = false,
  children,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames: sceneDuration } = useVideoConfig();

  // 计算动画进度 (0-1)
  const getProgress = () => {
    if (isExit) {
      // 出场动画: 从后往前
      const exitStart = Math.max(0, sceneDuration - durationInFrames);
      return Math.min(1, Math.max(0, (frame - exitStart) / durationInFrames));
    }
    // 入场动画: 从前往后
    return Math.min(1, frame / durationInFrames);
  };

  const progress = getProgress();
  const eased = 1 - Math.pow(1 - progress, 3); // cubic ease-out

  const getTransform = (): React.CSSProperties => {
    switch (type) {
      case 'fade':
        return { opacity: isExit ? 1 - eased : eased };

      case 'slideLeft':
        return {
          opacity: isExit ? 1 - eased : eased,
          transform: `translateX(${isExit ? -eased * 100 : (1 - eased) * 100}%)`,
        };

      case 'slideRight':
        return {
          opacity: isExit ? 1 - eased : eased,
          transform: `translateX(${isExit ? eased * 100 : -(1 - eased) * 100}%)`,
        };

      case 'slideUp':
        return {
          opacity: isExit ? 1 - eased : eased,
          transform: `translateY(${isExit ? -eased * 100 : (1 - eased) * 100}%)`,
        };

      case 'slideDown':
        return {
          opacity: isExit ? 1 - eased : eased,
          transform: `translateY(${isExit ? eased * 100 : -(1 - eased) * 100}%)`,
        };

      case 'zoomIn':
        return {
          opacity: isExit ? 1 - eased : eased,
          transform: `scale(${isExit ? 1 + eased * 0.3 : 0.7 + eased * 0.3})`,
        };

      case 'zoomOut':
        return {
          opacity: isExit ? 1 - eased : eased,
          transform: `scale(${isExit ? 0.7 + (1 - eased) * 0.3 : 1 - (1 - eased) * 0.3})`,
        };

      case 'dissolve':
        return { opacity: isExit ? 1 - eased * 0.8 : 1 - (1 - eased) * 0.8 };

      default:
        return { opacity: isExit ? 1 - eased : eased };
    }
  };

  return (
    <AbsoluteFill style={getTransform()}>
      {children}
    </AbsoluteFill>
  );
};

/**
 * 交叉淡入淡出过渡 (用于两个场景重叠切换)
 */
export const CrossFade: React.FC<{
  previousScene: React.ReactNode;
  nextScene: React.ReactNode;
  progress: number;
}> = ({ previousScene, nextScene, progress }) => {
  return (
    <>
      <AbsoluteFill style={{ opacity: 1 - progress }}>
        {previousScene}
      </AbsoluteFill>
      <AbsoluteFill style={{ opacity: progress }}>
        {nextScene}
      </AbsoluteFill>
    </>
  );
};

/**
 * 弹簧动画入场效果
 */
export const SpringEntrance: React.FC<{
  children: React.ReactNode;
  delayInFrames?: number;
  type?: 'scale' | 'slideUp' | 'slideLeft';
}> = ({ children, delayInFrames = 0, type = 'scale' }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({
    frame: frame - delayInFrames,
    fps,
    config: { damping: 12, stiffness: 100, mass: 0.8 },
  });

  const slideY = spring({
    frame: frame - delayInFrames,
    fps,
    config: { damping: 14, stiffness: 80, mass: 0.6 },
  });

  const opacity = interpolate(
    frame,
    [delayInFrames, delayInFrames + 8],
    [0, 1],
    { extrapolateRight: 'clamp' }
  );

  const getStyle = (): React.CSSProperties => {
    switch (type) {
      case 'scale':
        return { opacity, transform: `scale(${scale})` };
      case 'slideUp':
        return { opacity, transform: `translateY(${(1 - slideY) * 50}px)` };
      case 'slideLeft':
        return { opacity, transform: `translateX(${(1 - slideY) * 50}px)` };
      default:
        return { opacity };
    }
  };

  return <div style={getStyle()}>{children}</div>;
};

// 导出预设过渡配置
export const TRANSITION_PRESETS: Record<string, { type: TransitionType; duration: number }> = {
  fast: { type: 'fade', duration: 8 },
  normal: { type: 'fade', duration: 15 },
  slow: { type: 'fade', duration: 30 },
  slideLeft: { type: 'slideLeft', duration: 20 },
  slideRight: { type: 'slideRight', duration: 20 },
  slideUp: { type: 'slideUp', duration: 20 },
  zoom: { type: 'zoomIn', duration: 25 },
  dissolve: { type: 'dissolve', duration: 12 },
};
