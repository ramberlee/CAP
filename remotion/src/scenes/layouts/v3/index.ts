import { TechMultiPanel } from './TechMultiPanel';
import { ConnectedCards } from './ConnectedCards';
import { ArchitectureFlow } from './ArchitectureFlow';
import { StackHighlight } from './StackHighlight';
import { TimelineSteps } from './TimelineSteps';
import { StatsShowcase } from './StatsShowcase';
import { QuoteCard } from './QuoteCard';
import { ProgressSteps } from './ProgressSteps';
import { FeatureComparison } from './FeatureComparison';
import { DataCompare } from './DataCompare';
import { TerminalMockup } from './TerminalMockup';

export const v3LayoutRegistry: Record<string, React.FC<{ scene: any; theme: any }>> = {
  tech_multi_panel: TechMultiPanel,
  connected_cards: ConnectedCards,
  architecture_flow: ArchitectureFlow,
  stack_highlight: StackHighlight,
  timeline_steps: TimelineSteps,
  stats_showcase: StatsShowcase,
  quote_card: QuoteCard,
  progress_steps: ProgressSteps,
  feature_comparison: FeatureComparison,
  data_compare: DataCompare,
  terminal_mockup: TerminalMockup,
};

export {
  TechMultiPanel,
  ConnectedCards,
  ArchitectureFlow,
  StackHighlight,
  TimelineSteps,
  StatsShowcase,
  QuoteCard,
  ProgressSteps,
  FeatureComparison,
  DataCompare,
  TerminalMockup,
};
