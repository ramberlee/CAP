import React from 'react';
import { Scene, ThemePalette, LayoutType } from '../../types';
import { FONT_FAMILY, FONT_WEIGHT } from '../../styles/typography';
import { SceneFrame } from './_shared';
import { BlockRenderer } from '../../components/BlockRenderer';

/**
 * BlockTree — escape hatch. Renders an arbitrary block tree.
 * Used when the LLM wants full compositional freedom and none of the
 * 6 named layouts fit.
 */
export const BlockTreeScene: React.FC<{ scene: Scene; theme: ThemePalette }> = ({ scene, theme }) => {
  const content = scene.blocks ?? [];

  return (
    <SceneFrame theme={theme} englishLabel={scene.englishLabel}>
      <div
        style={{
          position: 'absolute',
          top: 96,
          left: 80,
          right: 80,
          bottom: 130,
          fontFamily: FONT_FAMILY,
          color: theme.text,
        }}
      >
        {scene.title && (
          <div
            style={{
              fontSize: 48,
              fontWeight: FONT_WEIGHT.bold,
              letterSpacing: 2,
              marginBottom: 24,
            }}
          >
            {scene.title}
          </div>
        )}
        <BlockRenderer blocks={content} theme={theme} />
      </div>
    </SceneFrame>
  );
};

(BlockTreeScene as any).layoutType = LayoutType.BlockTree;
