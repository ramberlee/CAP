// ===== 场景模板 =====
export * from './sceneTemplates';

// ===== 视频模板 =====
export * from './videoTemplates';

// ===== 快速使用工具 =====

import { CompositionPlan, Scene } from '../types';
import { createTechShowcaseVideo, createProductIntroVideo, createMinimalVideo } from './videoTemplates';

/**
 * 快速生成视频计划
 */
export function quickVideoPlan(
  template: 'techShowcase' | 'productIntro' | 'minimal',
  title: string,
  options?: { theme?: string; subtitle?: string }
): CompositionPlan {
  switch (template) {
    case 'techShowcase':
      return createTechShowcaseVideo({ title, ...options });
    case 'productIntro':
      return createProductIntroVideo(title, options);
    case 'minimal':
      return createMinimalVideo(title, [], options);
    default:
      return createMinimalVideo(title, [], options);
  }
}

/**
 * 拼接多个场景为完整视频
 */
export function composeVideo(
  scenes: Scene[],
  options: { theme?: string; title?: string; audioPath?: string } = {}
): CompositionPlan {
  return {
    title: options.title || 'Video',
    theme: options.theme || 'dark_tech_v3',
    scenes,
    audioPath: options.audioPath,
  };
}

/**
 * 创建标准 v3 科技风视频
 */
export function createV3TechVideo(
  title: string,
  contentScenes: Scene[],
  options?: { theme?: string }
): CompositionPlan {
  return composeVideo(
    [
      createTechShowcaseVideo({ title, ...options }).scenes[0], // 封面
      ...contentScenes,
      createTechShowcaseVideo({ title, ...options }).scenes.slice(-1)[0], // 结尾
    ],
    { title, theme: options?.theme || 'dark_tech_v3' }
  );
}
