import React from 'react';
import {
  AbsoluteFill,
  Sequence,
  useVideoConfig,
} from 'remotion';
import { Scene, ThemePalette } from '../../types';
import { SceneRenderer } from '../../VideoComposition';
import { TransitionType, TRANSITION_PRESETS } from './TransitionEffects';
import { getTheme } from '../../themes';

export interface SceneWithTransition extends Scene {
  transition?: {
    type?: TransitionType;
    duration?: number; // 秒
  };
}

interface SceneTransitionWrapperProps {
  scenes: SceneWithTransition[];
  theme?: string;
}

/**
 * 场景过渡包装器
 * 自动处理场景间的过渡动画，支持交叉淡入淡出
 */
export const SceneTransitionWrapper: React.FC<SceneTransitionWrapperProps> = ({
  scenes,
  theme: themeName = 'dark_glass',
}) => {
  const theme = getTheme(themeName);
  const { fps } = useVideoConfig();

  // 计算带过渡的场景时间线
  let cumulativeFrames = 0;
  const sceneTimeline = scenes.map((scene, index) => {
    const durationFrames = Math.round((scene.duration || 3) * fps);
    const transitionDuration = scene.transition?.duration
      ? Math.round(scene.transition.duration * fps)
      : TRANSITION_PRESETS.normal.duration;
    const transitionType = scene.transition?.type || TRANSITION_PRESETS.normal.type;

    const entry = {
      scene,
      index,
      startFrame: cumulativeFrames,
      durationFrames,
      transitionDuration,
      transitionType,
      endFrame: cumulativeFrames + durationFrames,
    };

    // 累积时间 = 开始 + 时长 - 过渡重叠
    cumulativeFrames += durationFrames - transitionDuration;
    return entry;
  });

  return (
    <AbsoluteFill style={{ backgroundColor: theme.background }}>
      {sceneTimeline.map((entry) => {
        // 计算与下一场景的重叠过渡区域
        const nextScene = sceneTimeline[entry.index + 1];
        const hasOverlap = nextScene && entry.transitionDuration > 0;
        const overlapStart = hasOverlap
          ? entry.endFrame - entry.transitionDuration
          : entry.endFrame;

        return (
          <Sequence
            key={`scene-${entry.index}`}
            from={entry.startFrame}
            durationInFrames={entry.durationFrames}
            layout="none"
          >
            {/* 场景内容 */}
            <SceneRenderer
              scene={entry.scene}
              theme={theme}
              startFrame={entry.startFrame}
              transitionType={entry.transitionType}
              transitionDuration={entry.transitionDuration}
              hasExitOverlap={hasOverlap}
              nextScene={nextScene?.scene}
            />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

/**
 * 获取场景的推荐过渡类型
 * 根据场景布局智能推荐合适的过渡效果
 */
export function getRecommendedTransition(scene: Scene): TransitionType {
  if (!scene.layout) return 'fade';

  const layoutTransitions: Record<string, TransitionType> = {
    title: 'zoomIn',
    title_card: 'zoomIn',
    tech_multi_panel: 'slideUp',
    connected_cards: 'slideRight',
    architecture_flow: 'fade',
    stack_highlight: 'slideUp',
    card_grid: 'slideUp',
    numbered_cards: 'slideRight',
    split_compare: 'dissolve',
    flow_diagram: 'fade',
    fan_out: 'slideLeft',
    doc_tree: 'slideUp',
  };

  return layoutTransitions[scene.layout] || 'fade';
}
