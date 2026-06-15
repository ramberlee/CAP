import React from "react";
import { Sequence } from "remotion";
import { getTheme } from "./themes";
import {
  TitleScene,
  TextSequenceScene,
  HighlightScene,
  ImageTextScene,
  BulletPointsScene,
  EndingScene,
} from "./scenes";
import { CompositionPlan, Scene } from "./types";

/**
 * VideoComposition renders a full video from a CompositionPlan.
 * Props are Record<string, unknown> as required by Remotion's Composition type.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const VideoComposition: React.FC<any> = (props) => {
  const plan = (props.plan as CompositionPlan) || (props.defaultProps?.plan as CompositionPlan | undefined);

  if (!plan || !plan.scenes) {
    return (
      <div
        style={{
          width: 1080,
          height: 1920,
          backgroundColor: "#000",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#fff",
          fontSize: 48,
          fontFamily: "sans-serif",
        }}
      >
        No composition plan provided
      </div>
    );
  }

  const theme = getTheme(plan.theme);
  let currentFrame = 0;

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        overflow: "hidden",
        fontFamily:
          '"Microsoft YaHei", "PingFang SC", "Noto Sans SC", sans-serif',
      }}
    >
      {plan.scenes.map((scene: Scene, index: number) => {
        const sceneDurationInFrames = Math.round(scene.duration * 30);
        const startFrame = currentFrame;
        currentFrame += sceneDurationInFrames;

        return (
          <Sequence
            key={index}
            from={startFrame}
            durationInFrames={sceneDurationInFrames}
          >
            <SceneRenderer scene={scene} theme={theme} />
          </Sequence>
        );
      })}
    </div>
  );
};

/** Route a single scene to its corresponding component */
const SceneRenderer: React.FC<{
  scene: Scene;
  theme: ReturnType<typeof getTheme>;
}> = ({ scene, theme }) => {
  switch (scene.type) {
    case "title":
      return (
        <TitleScene
          theme={theme}
          text={scene.text || ""}
          duration={scene.duration}
          animation={scene.animation}
        />
      );

    case "text_sequence":
      return (
        <TextSequenceScene
          theme={theme}
          lines={scene.lines || [scene.text || ""]}
          duration={scene.duration}
          animation={scene.animation}
        />
      );

    case "highlight":
      return (
        <HighlightScene
          theme={theme}
          text={scene.text || ""}
          duration={scene.duration}
          animation={scene.animation}
        />
      );

    case "image_text":
      return (
        <ImageTextScene
          theme={theme}
          text={scene.text || ""}
          imagePath={scene.imagePath}
          duration={scene.duration}
          animation={scene.animation}
        />
      );

    case "bullet_points":
      return (
        <BulletPointsScene
          theme={theme}
          items={scene.items || [scene.text || ""]}
          duration={scene.duration}
          animation={scene.animation}
        />
      );

    case "ending":
      return (
        <EndingScene
          theme={theme}
          text={scene.text || ""}
          duration={scene.duration}
          animation={scene.animation}
        />
      );

    default:
      return (
        <TitleScene
          theme={theme}
          text={scene.text || "Unknown scene type"}
          duration={scene.duration}
        />
      );
  }
};

export default VideoComposition;
