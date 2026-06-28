/* Layout scene registry — maps LayoutType values to React components. */
import { LayoutType } from '../../types';
import { TitleCardScene } from './TitleCardScene';
import { CardGridScene } from './CardGridScene';
import { NumberedCardsScene } from './NumberedCardsScene';
import { SplitCompareScene } from './SplitCompareScene';
import { FlowDiagramScene } from './FlowDiagramScene';
import { FanOutScene } from './FanOutScene';
import { DocTreeScene } from './DocTreeScene';
import { BlockTreeScene } from './BlockTreeScene';

export const layoutRegistry: Record<string, React.FC<{ scene: any; theme: any }>> = {
  [LayoutType.TitleCard]:     TitleCardScene,
  [LayoutType.CardGrid]:      CardGridScene,
  [LayoutType.NumberedCards]: NumberedCardsScene,
  [LayoutType.SplitCompare]:  SplitCompareScene,
  [LayoutType.FlowDiagram]:   FlowDiagramScene,
  [LayoutType.FanOut]:        FanOutScene,
  [LayoutType.DocTree]:       DocTreeScene,
  [LayoutType.BlockTree]:     BlockTreeScene,
};

export {
  TitleCardScene,
  CardGridScene,
  NumberedCardsScene,
  SplitCompareScene,
  FlowDiagramScene,
  FanOutScene,
  DocTreeScene,
  BlockTreeScene,
};
