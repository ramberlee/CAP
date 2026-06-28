import React from 'react';
import { useCurrentFrame } from 'remotion';
import { Scene, ThemePalette, LayoutType } from '../../types';
import { FONT_FAMILY, FONT_WEIGHT } from '../../styles/typography';
import { SceneFrame } from './_shared';

/**
 * FlowDiagram — architecture flow diagram (sample 9: "不是独立功能").
 *
 * Renders:
 *  - Left: input boxes (Prompt, Context)
 *  - Center-top: LLM box
 *  - Right: dashed Harness container with Agent loop and Harness boxes
 *  - Far right: MCP and Tool boxes
 *  - All connected by dashed lines
 *  - Bottom row: small legend pills
 *  - Floating callout text with arrow
 */
export const FlowDiagramScene: React.FC<{ scene: Scene; theme: ThemePalette }> = ({ scene, theme }) => {
  const frame = useCurrentFrame();

  const content = scene.flowDiagram ?? {
    title: scene.title ?? '',
    englishLabel: scene.englishLabel,
    inputs: [],
    llmLabel: 'LLM',
    llmSublabel: '主对话模型',
    harnessContainerTitle: 'HARNESS CONTAINER',
    agentLabel: 'AGENT LOOP',
    agentSublabel: 'Agent',
    harnessLabel: 'Harness',
    harnessSublabel: '运行/闭环',
    toolLabels: [],
    calloutText: '',
    bottomLegend: [],
    sceneSubtitle: scene.sceneSubtitle,
  };

  const titleProgress = Math.min(Math.max((frame / 24 - 0.1) / 0.5, 0), 1);
  const titleEase = 1 - Math.pow(1 - titleProgress, 3);

  // Helper: a small box component for the diagram
  const Box: React.FC<{
    label: string;
    sublabel?: string;
    accent?: 'orange' | 'cyan' | 'neutral';
    x: number; y: number; w: number; h: number;
    delay?: number;
    dashed?: boolean;
  }> = ({ label, sublabel, accent = 'neutral', x, y, w, h, delay = 0, dashed = false }) => {
    const prog = Math.min(Math.max((frame - 12 - delay) / 18, 0), 1);
    const ease = 1 - Math.pow(1 - prog, 3);
    const accentColor = accent === 'orange' ? (theme.accentOrange ?? '#FF6B35')
                       : accent === 'cyan'   ? (theme.accentCyan ?? '#00D4FF')
                       : null;
    return (
      <div
        style={{
          position: 'absolute',
          left: x, top: y, width: w, height: h,
          background: theme.glassSurface ?? 'rgba(255,255,255,0.05)',
          border: `1.5px ${dashed ? 'dashed' : 'solid'} ${accentColor ?? (theme.glassBorder ?? 'rgba(255,255,255,0.15)')}`,
          borderRadius: 12,
          padding: 12,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          textAlign: 'center',
          fontFamily: FONT_FAMILY,
          color: accentColor ?? theme.text,
          opacity: ease,
          transform: `scale(${0.92 + ease * 0.08})`,
          boxShadow: accentColor ? `0 0 20px ${accentColor}22` : 'none',
        }}
      >
        <div style={{ fontSize: 18, fontWeight: FONT_WEIGHT.bold, letterSpacing: 0.5 }}>
          {label}
        </div>
        {sublabel && (
          <div style={{ fontSize: 12, color: theme.textSecondary, marginTop: 4 }}>
            {sublabel}
          </div>
        )}
      </div>
    );
  };

  return (
    <SceneFrame theme={theme} englishLabel={content.englishLabel}>
      {/* Title */}
      <div
        style={{
          position: 'absolute',
          top: 80,
          left: 80,
          fontFamily: FONT_FAMILY,
          color: theme.text,
          opacity: titleEase,
        }}
      >
        <div
          style={{
            fontSize: 48,
            fontWeight: FONT_WEIGHT.bold,
            letterSpacing: 2,
          }}
        >
          {content.title}
        </div>
      </div>

      {/* Section label "INPUTS TO MODEL" */}
      <div
        style={{
          position: 'absolute',
          top: 220,
          left: 80,
          fontFamily: FONT_FAMILY,
          fontSize: 12,
          fontWeight: FONT_WEIGHT.semibold,
          color: theme.textSecondary,
          letterSpacing: 2,
          opacity: Math.min(Math.max((frame - 5) / 12, 0), 1),
        }}
      >
        INPUTS TO MODEL
      </div>

      {/* Left input boxes */}
      {(content.inputs ?? []).map((inp, i) => (
        <Box
          key={i}
          label={inp.label}
          sublabel={inp.sublabel}
          accent={i === 0 ? 'orange' : 'cyan'}
          x={80}
          y={260 + i * 100}
          w={200}
          h={80}
          delay={i * 4}
        />
      ))}

      {/* Center: LLM box */}
      <Box
        label={content.llmLabel}
        sublabel={content.llmSublabel ?? '生成/推理/反馈'}
        accent="orange"
        x={420}
        y={340}
        w={220}
        h={100}
        delay={10}
      />

      {/* Harness container (dashed) */}
      <div
        style={{
          position: 'absolute',
          left: 720,
          top: 220,
          width: 460,
          height: 360,
          border: '2px dashed rgba(255,71,87,0.5)',
          borderRadius: 18,
          background: 'rgba(255,71,87,0.04)',
          padding: 16,
          opacity: Math.min(Math.max((frame - 14) / 20, 0), 1),
        }}
      >
        <div
          style={{
            position: 'absolute',
            top: 14,
            left: 24,
            fontFamily: FONT_FAMILY,
            fontSize: 12,
            fontWeight: FONT_WEIGHT.bold,
            color: theme.accentRed ?? '#FF4757',
            letterSpacing: 2,
          }}
        >
          {content.harnessContainerTitle ?? 'HARNESS CONTAINER'}
        </div>
        <Box
          label={content.agentLabel}
          sublabel={content.agentSublabel}
          x={20}
          y={60}
          w={200}
          h={80}
          delay={18}
        />
        <Box
          label={content.harnessLabel}
          sublabel={content.harnessSublabel}
          x={240}
          y={60}
          w={200}
          h={80}
          delay={22}
        />
        <Box
          label="Skill"
          sublabel="封装命令面"
          x={20}
          y={180}
          w={200}
          h={80}
          accent="orange"
          delay={26}
        />
        <Box
          label="Harness 链路执行"
          sublabel=""
          x={240}
          y={180}
          w={200}
          h={80}
          delay={30}
        />
      </div>

      {/* Far right: MCP / Tool boxes */}
      {(content.toolLabels ?? []).map((tool, i) => (
        <Box
          key={i}
          label={tool.label}
          sublabel={tool.sublabel}
          accent="cyan"
          x={1240}
          y={280 + i * 110}
          w={180}
          h={80}
          delay={14 + i * 4}
        />
      ))}

      {/* Bottom legend row */}
      <div
        style={{
          position: 'absolute',
          bottom: 130,
          left: 80,
          right: 80,
          display: 'flex',
          gap: 24,
          justifyContent: 'center',
          opacity: Math.min(Math.max((frame - 40) / 18, 0), 1),
        }}
      >
        {(content.bottomLegend ?? []).map((entry, i) => {
          const accentColor = entry.tone === 'orange' ? (theme.accentOrange ?? '#FF6B35')
                             : entry.tone === 'cyan'   ? (theme.accentCyan ?? '#00D4FF')
                             : null;
          return (
            <div
              key={i}
              style={{
                padding: '10px 20px',
                background: theme.glassSurface ?? 'rgba(255,255,255,0.05)',
                border: `1px solid ${accentColor ?? (theme.glassBorder ?? 'rgba(255,255,255,0.12)')}`,
                borderRadius: 999,
                fontFamily: FONT_FAMILY,
                fontSize: 14,
                color: theme.text,
                letterSpacing: 0.5,
              }}
            >
              {entry.label}
            </div>
          );
        })}
      </div>

      {/* Floating callout */}
      {content.calloutText && (
        <div
          style={{
            position: 'absolute',
            right: 200,
            bottom: 200,
            padding: '12px 20px',
            background: 'linear-gradient(90deg, rgba(255,107,53,0.25), rgba(0,212,255,0.15))',
            border: '1px solid rgba(255,107,53,0.4)',
            borderRadius: 10,
            fontFamily: FONT_FAMILY,
            fontSize: 20,
            fontWeight: FONT_WEIGHT.bold,
            color: theme.text,
            opacity: Math.min(Math.max((frame - 45) / 16, 0), 1),
          }}
        >
          {content.calloutText}
        </div>
      )}

      {/* SVG dashed connector lines */}
      <svg
        style={{
          position: 'absolute',
          inset: 0,
          width: '100%',
          height: '100%',
          pointerEvents: 'none',
          opacity: Math.min(Math.max((frame - 20) / 20, 0), 0.6),
        }}
        viewBox="0 0 1920 1080"
        preserveAspectRatio="none"
      >
        {/* Input 1 → LLM */}
        <path d="M 280 300 L 420 380" stroke={theme.accentOrange ?? '#FF6B35'} strokeWidth="1.5" strokeDasharray="5 5" fill="none" />
        {/* Input 2 → LLM */}
        <path d="M 280 360 L 420 400" stroke={theme.accentCyan ?? '#00D4FF'} strokeWidth="1.5" strokeDasharray="5 5" fill="none" />
        {/* LLM → Harness Agent */}
        <path d="M 640 390 L 740 320" stroke="rgba(255,255,255,0.4)" strokeWidth="1.5" strokeDasharray="5 5" fill="none" />
        {/* LLM → Harness Harness */}
        <path d="M 640 410 L 960 320" stroke="rgba(255,255,255,0.4)" strokeWidth="1.5" strokeDasharray="5 5" fill="none" />
        {/* Agent → MCP */}
        <path d="M 920 320 L 1240 320" stroke={theme.accentCyan ?? '#00D4FF'} strokeWidth="1.5" strokeDasharray="5 5" fill="none" />
        {/* Harness → Tool */}
        <path d="M 960 360 L 1240 400" stroke={theme.accentCyan ?? '#00D4FF'} strokeWidth="1.5" strokeDasharray="5 5" fill="none" />
      </svg>
    </SceneFrame>
  );
};

(FlowDiagramScene as any).layoutType = LayoutType.FlowDiagram;
