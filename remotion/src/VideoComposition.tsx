import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
} from 'remotion';
import { CompositionPlan, Scene, SceneType } from './types';
import { ThemePalette } from './themes';
import { getTheme } from './themes';
import { Subtitle } from './components/Subtitle';
import { DotGridBackground } from './components/DotGridBackground';
import { isDarkGlassTheme } from './themes';

// 过渡类型
export type TransitionType = 'fade' | 'slideLeft' | 'slideRight' | 'slideUp' | 'slideDown' | 'zoomIn' | 'zoomOut' | 'dissolve';

// Legacy v1 scene components
import { TitleScene } from './scenes/legacy/TitleScene';
import { BulletScene } from './scenes/legacy/BulletScene';
import { SectionTitleScene } from './scenes/legacy/SectionTitleScene';
import { DataScene } from './scenes/legacy/DataScene';
import { QuoteScene } from './scenes/legacy/QuoteScene';
import { ComparisonScene } from './scenes/legacy/ComparisonScene';
import { TimelineScene } from './scenes/legacy/TimelineScene';
import { HighlightScene } from './scenes/legacy/HighlightScene';
import { ImageCaptionScene } from './scenes/legacy/ImageCaptionScene';
import { EndingScene } from './scenes/legacy/EndingScene';

// v2 layout components
import { layoutRegistry } from './scenes/layouts';
// v3 layout components (advanced tech layouts)
import { v3LayoutRegistry } from './scenes/layouts/v3';

// ───────────────────────────────────────────────────────────────────────
//  Scene registries
// ───────────────────────────────────────────────────────────────────────

type LegacySceneComponent = React.FC<{
  scene: Scene;
  theme: ThemePalette;
  frame: number;
  fps: number;
  startFrame: number;
}>;

const legacySceneRegistry: Record<SceneType, LegacySceneComponent> = {
  [SceneType.Title]: TitleScene,
  [SceneType.Bullet]: BulletScene,
  [SceneType.SectionTitle]: SectionTitleScene,
  [SceneType.DataCard]: DataScene,
  [SceneType.Quote]: QuoteScene,
  [SceneType.Comparison]: ComparisonScene,
  [SceneType.Timeline]: TimelineScene,
  [SceneType.Highlight]: HighlightScene,
  [SceneType.ImageCaption]: ImageCaptionScene,
  [SceneType.Ending]: EndingScene,
};

// ===== 过渡包装器组件 =====================================================
const SceneTransition: React.FC<{
  type: TransitionType;
  duration: number;
  children: React.ReactNode;
}> = ({ type, duration, children }) => {
  const frame = useCurrentFrame();
  const { durationInFrames: totalFrames } = useVideoConfig();

  // 入场动画 (0 -> duration)
  const entryProgress = Math.min(1, frame / duration);
  const entryEased = 1 - Math.pow(1 - entryProgress, 3);

  // 出场动画 (totalFrames - duration -> totalFrames)
  const exitStart = Math.max(0, totalFrames - duration);
  const exitProgress = Math.min(1, Math.max(0, (frame - exitStart) / duration));
  const exitEased = 1 - Math.pow(1 - exitProgress, 3);

  const getStyle = (): React.CSSProperties => {
    // 合并入场和出场效果
    switch (type) {
      case 'fade':
        return {
          opacity: entryEased * (1 - exitEased * 0.5),
        };
      case 'slideUp':
        return {
          opacity: entryEased,
          transform: `translateY(${-(1 - entryEased) * 10}%)`,
        };
      case 'slideLeft':
        return {
          opacity: entryEased,
          transform: `translateX(${(1 - entryEased) * 10}%)`,
        };
      case 'slideRight':
        return {
          opacity: entryEased,
          transform: `translateX(${-(1 - entryEased) * 10}%)`,
        };
      case 'zoomIn':
        return {
          opacity: entryEased,
          transform: `scale(${0.9 + entryEased * 0.1})`,
        };
      default:
        return { opacity: entryEased };
    }
  };

  return <AbsoluteFill style={getStyle()}>{children}</AbsoluteFill>;
};

// ───────────────────────────────────────────────────────────────────────
//  SceneRenderer — with transition support
// ───────────────────────────────────────────────────────────────────────

export interface SceneRendererProps {
  scene: Scene;
  theme: ThemePalette;
  startFrame: number;
  transitionType?: TransitionType;
  transitionDuration?: number;
  hasExitOverlap?: boolean;
  nextScene?: Scene;
}

export const SceneRenderer: React.FC<SceneRendererProps> = ({
  scene,
  theme,
  startFrame,
  transitionType = 'fade',
  transitionDuration = 15,
  hasExitOverlap = false,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const sceneDurationFrames = Math.round((scene.duration || 0) * fps);

  // 根据布局类型选择过渡效果
  const getTransitionForScene = (): TransitionType => {
    if (!scene.layout) return 'fade';
    const transitions: Record<string, TransitionType> = {
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
      timeline_steps: 'slideUp',
      stats_showcase: 'zoomIn',
      quote_card: 'fade',
      progress_steps: 'slideRight',
      feature_comparison: 'slideUp',
      data_compare: 'slideUp',
      terminal_mockup: 'fade',
    };
    return transitions[scene.layout] || transitionType;
  };

  const actualTransition = getTransitionForScene();

  // v3 layout path (advanced tech layouts, highest priority)
  if (scene.layout && v3LayoutRegistry[scene.layout]) {
    const LayoutComponent = v3LayoutRegistry[scene.layout];
    // v3 components manage their own background effects and subtitles
    return (
      <SceneTransition type={actualTransition} duration={transitionDuration}>
        <LayoutComponent scene={scene} theme={theme} />
      </SceneTransition>
    );
  }

  // v2 layout path
  if (scene.layout && layoutRegistry[scene.layout]) {
    const LayoutComponent = layoutRegistry[scene.layout];
    return (
      <SceneTransition type={actualTransition} duration={transitionDuration}>
        {isDarkGlassTheme(theme) && (
          <DotGridBackground
            theme={theme}
            sceneDurationInFrames={sceneDurationFrames}
          />
        )}
        <LayoutComponent scene={scene} theme={theme} />
        {/* Bottom caption overlay */}
        <Subtitle
          text={scene.sceneSubtitle}
          chunks={scene.subtitleChunks}
          theme={theme}
          sceneDurationInFrames={sceneDurationFrames}
          glassBackground={isDarkGlassTheme(theme)}
        />
      </SceneTransition>
    );
  }

  // Legacy v1 path
  if (scene.type && legacySceneRegistry[scene.type]) {
    const Component = legacySceneRegistry[scene.type];
    return (
      <SceneTransition type={transitionType} duration={transitionDuration}>
        <Component
          scene={scene}
          theme={theme}
          frame={frame}
          fps={fps}
          startFrame={startFrame}
        />
      </SceneTransition>
    );
  }

  // Unknown — render empty frame
  return <AbsoluteFill style={{ backgroundColor: theme.background }} />;
};

// ───────────────────────────────────────────────────────────────────────
//  VideoComposition
// ───────────────────────────────────────────────────────────────────────

const VideoComposition: React.FC<{ plan?: CompositionPlan }> = ({
  plan = { theme: 'dark_glass', scenes: [] },
}) => {
  const theme = getTheme(plan.theme);
  const { fps } = useVideoConfig();

  let cumulativeFrames = 0;
  const sceneEntries = (plan.scenes || []).map((scene) => {
    const durationFrames = Math.round((scene.duration || 3) * fps);
    const entry = { scene, startFrame: cumulativeFrames, durationFrames };
    cumulativeFrames += durationFrames;
    return entry;
  });

  return (
    <AbsoluteFill style={{ backgroundColor: theme.background }}>
      {sceneEntries.map((entry, index) => (
        <Sequence
          key={`scene-${index}`}
          from={entry.startFrame}
          durationInFrames={entry.durationFrames}
        >
          <SceneRenderer
            scene={entry.scene}
            theme={theme}
            startFrame={entry.startFrame}
          />
        </Sequence>
      ))}
      {plan.audioPath && <Audio src={staticFile(plan.audioPath)} />}
    </AbsoluteFill>
  );
};

export default VideoComposition;
