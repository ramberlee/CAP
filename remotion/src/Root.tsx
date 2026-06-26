import React from 'react';
import { Composition, registerRoot } from 'remotion';
import VideoComposition from './VideoComposition';

const FPS = 24;
const WIDTH = 1920;
const HEIGHT = 1080;
const DEFAULT_DURATION = 30 * FPS; // 30 seconds default

const defaultPlan = {
  theme: 'dark_tech' as const,
  scenes: [
    { type: 'title' as const, duration: 4, title: '示例视频', subtitle: '科技前沿 · 深度解读' },
    { type: 'bullet' as const, duration: 5, title: '核心要点', items: ['第一点重要发现', '第二点关键数据', '第三点未来展望'] },
    { type: 'ending' as const, duration: 4, title: '感谢观看', items: ['要点总结一', '要点总结二', '要点总结三'], subtitle: '关注我们 · 获取更多' },
  ],
};

const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="CAPVideo"
      component={VideoComposition}
      durationInFrames={DEFAULT_DURATION}
      fps={FPS}
      width={WIDTH}
      height={HEIGHT}
      defaultProps={{ plan: defaultPlan }}
    />
  );
};

registerRoot(RemotionRoot);
