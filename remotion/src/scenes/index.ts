/* Scene component exports.

Two coexisting systems:

- Legacy v1 (10 flat scene types) — kept under `./legacy/` for backward compatibility.
- Layouts v2 (7 named layouts + block_tree escape hatch) — under `./layouts/`.
*/

// Shared
export { SceneWrapper } from './SceneWrapper';

// Legacy v1 — preserved
export { TitleScene } from './legacy/TitleScene';
export { BulletScene } from './legacy/BulletScene';
export { SectionTitleScene } from './legacy/SectionTitleScene';
export { DataScene } from './legacy/DataScene';
export { QuoteScene } from './legacy/QuoteScene';
export { ComparisonScene } from './legacy/ComparisonScene';
export { TimelineScene } from './legacy/TimelineScene';
export { HighlightScene } from './legacy/HighlightScene';
export { ImageCaptionScene } from './legacy/ImageCaptionScene';
export { EndingScene } from './legacy/EndingScene';

// v2 layouts
export {
  TitleCardScene,
  CardGridScene,
  NumberedCardsScene,
  SplitCompareScene,
  FlowDiagramScene,
  FanOutScene,
  DocTreeScene,
  BlockTreeScene,
  layoutRegistry,
} from './layouts';
