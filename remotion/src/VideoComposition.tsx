import React from 'react';
import { AbsoluteFill, Sequence, useCurrentFrame, useVideoConfig } from 'remotion';
import { CompositionPlan, Scene, SceneType } from './types';
import { getTheme, ThemePalette } from './themes';
import { TitleScene } from './scenes/TitleScene';
import { BulletScene } from './scenes/BulletScene';
import { SectionTitleScene } from './scenes/SectionTitleScene';
import { DataScene } from './scenes/DataScene';
import { QuoteScene } from './scenes/QuoteScene';
import { ComparisonScene } from './scenes/ComparisonScene';
import { TimelineScene } from './scenes/TimelineScene';
import { HighlightScene } from './scenes/HighlightScene';
import { ImageCaptionScene } from './scenes/ImageCaptionScene';
import { EndingScene } from './scenes/EndingScene';

// Scene component registry
type SceneComponent = React.FC<{
  scene: Scene;
  theme: ThemePalette;
  frame: number;
  fps: number;
  startFrame: number;
}>;

const sceneRegistry: Record<SceneType, SceneComponent> = {
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

const SceneRenderer: React.FC<{
  scene: Scene;
  theme: ThemePalette;
  startFrame: number;
}> = ({ scene, theme, startFrame }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const Component = sceneRegistry[scene.type];

  if (!Component) {
    return <AbsoluteFill style={{ backgroundColor: theme.background }} />;
  }

  return (
    <Component
      scene={scene}
      theme={theme}
      frame={frame}
      fps={fps}
      startFrame={startFrame}
    />
  );
};

const VideoComposition: React.FC<{ plan?: CompositionPlan }> = ({
  plan = { theme: 'dark_tech', scenes: [] },
}) => {
  const theme = getTheme(plan.theme);
  const { fps } = useVideoConfig();

  let cumulativeFrames = 0;
  const sceneEntries = (plan.scenes || []).map((scene) => {
    const durationFrames = Math.round(scene.duration * fps);
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
    </AbsoluteFill>
  );
};

export default VideoComposition;
