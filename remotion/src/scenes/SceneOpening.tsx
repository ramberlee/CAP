import {
	AbsoluteFill,
	useCurrentFrame,
	useVideoConfig,
	spring,
	interpolate,
} from 'remotion';
import React, { useMemo } from 'react';

// ─── NeuralAgent SVG Icon ──────────────────────────────────────────────────────
// A stylized neural network node fused with a mouse cursor
const NeuralAgentIcon: React.FC<{
	scale: number;
	opacity: number;
	glowIntensity: number;
}> = ({ scale, opacity, glowIntensity }) => {
	return (
		<svg
			viewBox="0 0 200 200"
			width={180 * scale}
			height={180 * scale}
			style={{
				opacity,
				filter: `drop-shadow(0 0 ${8 * glowIntensity}px #7c3aed) drop-shadow(0 0 ${24 * glowIntensity}px rgba(124, 58, 237, 0.4))`,
			}}
		>
			<defs>
				<radialGradient id="centerGlow" cx="50%" cy="50%" r="50%">
					<stop offset="0%" stopColor="#c4b5fd" stopOpacity={0.9} />
					<stop offset="40%" stopColor="#8b5cf6" stopOpacity={0.6} />
					<stop offset="100%" stopColor="#7c3aed" stopOpacity={0} />
				</radialGradient>
				<radialGradient id="nodeGlow" cx="50%" cy="50%" r="50%">
					<stop offset="0%" stopColor="#a78bfa" stopOpacity={0.9} />
					<stop offset="100%" stopColor="#6d28d9" stopOpacity={0} />
				</radialGradient>
				<linearGradient id="lineGrad" x1="0%" y1="0%" x2="100%" y2="100%">
					<stop offset="0%" stopColor="#7c3aed" stopOpacity={0.8} />
					<stop offset="50%" stopColor="#a78bfa" stopOpacity={0.9} />
					<stop offset="100%" stopColor="#7c3aed" stopOpacity={0.8} />
				</linearGradient>
				<filter id="glow">
					<feGaussianBlur stdDeviation="3" result="blur" />
					<feMerge>
						<feMergeNode in="blur" />
						<feMergeNode in="SourceGraphic" />
					</feMerge>
				</filter>
			</defs>

			{/* Center glow aura */}
			<circle cx="100" cy="100" r="50" fill="url(#centerGlow)" opacity={0.4 * glowIntensity} />

			{/* Neural network connections */}
			<g stroke="url(#lineGrad)" strokeWidth="2.5" strokeLinecap="round" fill="none" filter="url(#glow)">
				{/* Central hub connections */}
				<line x1="100" y1="100" x2="50" y2="35" opacity={0.9} />
				<line x1="100" y1="100" x2="150" y2="35" opacity={0.9} />
				<line x1="100" y1="100" x2="30" y2="135" opacity={0.85} />
				<line x1="100" y1="100" x2="170" y2="135" opacity={0.85} />
				<line x1="100" y1="100" x2="75" y2="180" opacity={0.8} />
				<line x1="100" y1="100" x2="125" y2="180" opacity={0.8} />
				{/* Outer ring connections */}
				<line x1="50" y1="35" x2="150" y2="35" opacity={0.5} />
				<line x1="30" y1="135" x2="75" y2="180" opacity={0.5} />
				<line x1="170" y1="135" x2="125" y2="180" opacity={0.5} />
				<line x1="50" y1="35" x2="30" y2="135" opacity={0.4} />
				<line x1="150" y1="35" x2="170" y2="135" opacity={0.4} />
			</g>

			{/* Neural nodes */}
			<g filter="url(#glow)">
				{/* Center node - the mouse cursor fusion */}
				<circle cx="100" cy="100" r="26" fill="url(#nodeGlow)" />
				<circle cx="100" cy="100" r="14" fill="#8b5cf6" stroke="#c4b5fd" strokeWidth="2.5" />
				{/* Cursor arrow inside center - stylized */}
				<path
					d="M94 88 L94 112 L99 107 L105 113 L108 110 L102 104 L109 101 Z"
					fill="#e0e7ff"
					stroke="#c4b5fd"
					strokeWidth="1.2"
					opacity={0.95}
				/>
				{/* Small cursor dot */}
				<circle cx="94" cy="88" r="3" fill="#e0e7ff" opacity={0.8} />

				{/* Outer nodes */}
				<circle cx="50" cy="35" r="9" fill="#7c3aed" stroke="#a78bfa" strokeWidth="1.5" />
				<circle cx="150" cy="35" r="9" fill="#7c3aed" stroke="#a78bfa" strokeWidth="1.5" />
				<circle cx="30" cy="135" r="9" fill="#7c3aed" stroke="#a78bfa" strokeWidth="1.5" />
				<circle cx="170" cy="135" r="9" fill="#7c3aed" stroke="#a78bfa" strokeWidth="1.5" />
				<circle cx="75" cy="180" r="8" fill="#6d28d9" stroke="#a78bfa" strokeWidth="1.5" />
				<circle cx="125" cy="180" r="8" fill="#6d28d9" stroke="#a78bfa" strokeWidth="1.5" />
			</g>

			{/* Node pulse rings */}
			{[
				{ cx: 50, cy: 35 },
				{ cx: 150, cy: 35 },
				{ cx: 100, cy: 100 },
			].map((node, i) => (
				<circle
					key={i}
					cx={node.cx}
					cy={node.cy}
					r={14 + 6 * glowIntensity}
					fill="none"
					stroke="#a78bfa"
					strokeWidth="1"
					opacity={0.3 * glowIntensity}
				/>
			))}
		</svg>
	);
};

// ─── Particle ──────────────────────────────────────────────────────────────────
interface ParticleProps {
	index: number;
	total: number;
	frame: number;
	startFrame: number;
	duration: number;
}

const Particle: React.FC<ParticleProps> = ({ index, total, frame, startFrame, duration }) => {
	const localFrame = frame - startFrame;
	if (localFrame < 0 || localFrame > duration) return null;

	// Deterministic random values based on index
	const seed = index * 7.3;
	const r1 = Math.sin(seed) * 0.5 + 0.5;
	const r2 = Math.sin(seed * 1.7) * 0.5 + 0.5;
	const r3 = Math.sin(seed * 2.3) * 0.5 + 0.5;

	const progress = spring({
		frame: localFrame,
		fps: 30,
		config: {
			damping: 14 + r1 * 8,
			mass: 0.3 + r2 * 0.5,
			stiffness: 55 + r3 * 30,
		},
	});

	// Distribute particles around the edge of the screen
	const angle = (index / total) * Math.PI * 2 + r1 * 0.3;
	const radius = 380 + r2 * 200;
	const startX = 480 + Math.cos(angle) * radius;
	const startY = 270 + Math.sin(angle) * radius;
	// Target: center of the icon area (with slight randomness)
	const targetX = 480 + (r1 - 0.5) * 40;
	const targetY = 230 + (r2 - 0.5) * 40;

	const x = interpolate(progress, [0, 1], [startX, targetX]);
	const y = interpolate(progress, [0, 1], [startY, targetY]);
	const opacity = interpolate(progress, [0, 0.05, 0.85, 1], [0, 1, 0.8, 0]);
	const size = interpolate(progress, [0, 0.6, 1], [2.5, 3.5, 1]);

	const hue = 250 + r3 * 30; // purple-blue range
	const sat = 70 + r2 * 20;
	const light = 60 + r1 * 20;

	return (
		<circle
			cx={x}
			cy={y}
			r={size}
			fill={`hsl(${hue}, ${sat}%, ${light}%)`}
			style={{
				opacity,
				filter: `drop-shadow(0 0 ${3 + r1 * 4}px hsla(${hue}, 80%, 70%, 0.6))`,
			}}
		/>
	);
};

// ─── Typing Text with Glow Trail ───────────────────────────────────────────────
const TypingText: React.FC<{
	text: string;
	startFrame: number;
	letterDuration: number;
	color: string;
	glowColor: string;
	fontSize: number;
	delay?: number;
}> = ({ text, startFrame, letterDuration, color, glowColor, fontSize, delay = 0 }) => {
	const frame = useCurrentFrame();
	const localFrame = frame - startFrame - delay;

	if (localFrame < 0) return null;

	const totalLetters = text.length;
	const totalDuration = totalLetters * letterDuration + 25;

	const chars: React.ReactNode[] = [];
	for (let i = 0; i < totalLetters; i++) {
		const charAppear = i * letterDuration;
		if (localFrame < charAppear) break;

		const charAge = localFrame - charAppear;
		const opacity = Math.min(1, charAge / 3);
		const glowOpacity = Math.max(0, 1 - charAge / 15);

		chars.push(
			<span
				key={i}
				style={{
					opacity,
					color,
					textShadow: glowOpacity > 0.01
						? `0 0 ${4 + glowOpacity * 14}px ${glowColor}, 0 0 ${2 + glowOpacity * 8}px ${glowColor}, 0 0 ${glowOpacity * 4}px rgba(255,255,255,0.3)`
						: `0 0 4px ${glowColor}`,
					transition: 'none',
				}}
			>
				{text[i] === ' ' ? ' ' : text[i]}
			</span>
		);
	}

	const fadeOutStart = totalDuration - 15;

	return (
		<div
			style={{
				fontSize,
				fontWeight: 700,
				fontFamily: "'Inter', 'Segoe UI', -apple-system, sans-serif",
				letterSpacing: '0.06em',
				opacity: localFrame < fadeOutStart ? 1 : interpolate(localFrame - fadeOutStart, [0, 15], [1, 0], { extrapolateRight: 'clamp' }),
			}}
		>
			{chars}
		</div>
	);
};

// ─── FadeInText ────────────────────────────────────────────────────────────────
const FadeInText: React.FC<{
	text: string;
	startFrame: number;
	fontSize: number;
	color: string;
}> = ({ text, startFrame, fontSize, color }) => {
	const frame = useCurrentFrame();
	const localFrame = frame - startFrame;
	if (localFrame < 0) return null;

	const opacity = interpolate(localFrame, [0, 20], [0, 1], {
		extrapolateRight: 'clamp',
	});
	const y = interpolate(localFrame, [0, 20], [15, 0], {
		extrapolateRight: 'clamp',
	});

	return (
		<div
			style={{
				fontSize,
				fontWeight: 400,
				fontFamily: "'Inter', 'Segoe UI', -apple-system, sans-serif",
				color,
				opacity,
				transform: `translateY(${y}px)`,
				letterSpacing: '0.18em',
				textShadow: `0 0 8px rgba(124, 58, 237, 0.3)`,
			}}
		>
			{text}
		</div>
	);
};

// ─── Ambient Floating Particles (background) ───────────────────────────────────
const AmbientParticles: React.FC<{ frame: number }> = ({ frame }) => {
	const particles = useMemo(() => {
		return Array.from({ length: 25 }, (_, i) => ({
			x: (Math.sin(i * 137.5) * 0.5 + 0.5) * 960,
			y: (Math.cos(i * 99.3) * 0.5 + 0.5) * 540,
			size: 1 + (Math.sin(i * 53.7) * 0.5 + 0.5) * 2.5,
			speed: 0.15 + (Math.sin(i * 71.1) * 0.5 + 0.5) * 0.4,
			drift: Math.sin(i * 43.9) * Math.PI,
			hue: 250 + (Math.sin(i * 67.3) * 0.5 + 0.5) * 30,
			alpha: 0.15 + (Math.sin(i * 89.7) * 0.5 + 0.5) * 0.2,
		}));
	}, []);

	return (
		<svg width="960" height="540" style={{ position: 'absolute', top: 0, left: 0 }}>
			{particles.map((p, i) => {
				const yOffset = Math.sin(frame * 0.008 * p.speed + p.drift) * 20;
				const xOffset = Math.cos(frame * 0.006 * p.speed + p.drift * 0.7) * 12;
				const twinkle = 0.6 + Math.sin(frame * 0.03 + i * 2.1) * 0.4;
				return (
					<circle
						key={i}
						cx={p.x + xOffset}
						cy={p.y + yOffset}
						r={p.size}
						fill={`hsla(${p.hue}, 60%, 65%, ${p.alpha * twinkle})`}
					/>
				);
			})}
		</svg>
	);
};

// ─── Scene Opening ─────────────────────────────────────────────────────────────
export const SceneOpening: React.FC = () => {
	const frame = useCurrentFrame();
	const { fps } = useVideoConfig();

	// Timing (in frames at 30fps)
	const PARTICLE_START = 0;
	const PARTICLE_DURATION = 45;
	const ICON_APPEAR = 25;
	const TITLE_START = 70;
	const SUBTITLE_START = 100;

	// Icon spring animation - larger, with bounce
	const iconSpring = spring({
		frame: frame - ICON_APPEAR,
		fps,
		config: {
			damping: 11,
			mass: 0.5,
			stiffness: 85,
		},
	});

	const iconScale = interpolate(iconSpring, [0, 1], [0.2, 1]);
	const iconOpacity = interpolate(frame - ICON_APPEAR, [0, 5], [0, 1], {
		extrapolateRight: 'clamp',
	});
	const glowIntensity = interpolate(
		spring({
			frame: frame - ICON_APPEAR,
			fps,
			config: { damping: 12, mass: 1.2, stiffness: 40 },
		}),
		[0, 1],
		[0, 1]
	);

	// Screen pulse effect after icon forms
	const pulseFrame = frame - ICON_APPEAR - 15;
	const pulseOpacity = pulseFrame >= 0
		? interpolate(
			spring({
				frame: pulseFrame,
				fps,
				config: { damping: 3, mass: 0.6, stiffness: 120 },
			}),
			[0, 1],
			[0, 0.12]
		)
		: 0;

	// Scene end fade out
	const sceneEndFade = frame >= 135
		? interpolate(frame - 135, [0, 15], [1, 0], { extrapolateRight: 'clamp' })
		: 1;

	return (
		<AbsoluteFill style={{ overflow: 'hidden' }}>
			{/* Dark gradient background */}
			<AbsoluteFill
				style={{
					background: 'linear-gradient(135deg, #0a0a1a 0%, #1a0a2e 45%, #0d0d2b 100%)',
				}}
			/>

			{/* Subtle vignette overlay */}
			<AbsoluteFill
				style={{
					background: 'radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,0.5) 100%)',
				}}
			/>

			{/* Ambient floating particles */}
			<AmbientParticles frame={frame} />

			{/* Pulse effect after icon forms */}
			<AbsoluteFill
				style={{
					background: `radial-gradient(circle at 50% 38%, #7c3aed 0%, transparent 55%)`,
					opacity: pulseOpacity,
				}}
			/>

			{/* Particle system - converging particles */}
			<svg width="960" height="540" style={{ position: 'absolute', top: 0, left: 0 }}>
				{Array.from({ length: 80 }, (_, i) => (
					<Particle
						key={i}
						index={i}
						total={80}
						frame={frame}
						startFrame={PARTICLE_START}
						duration={PARTICLE_DURATION}
					/>
				))}
			</svg>

			{/* Scene fade wrapper */}
			<AbsoluteFill style={{ opacity: sceneEndFade }}>
				{/* Central content */}
				<div
					style={{
						position: 'absolute',
						top: '50%',
						left: '50%',
						transform: 'translate(-50%, -50%)',
						display: 'flex',
						flexDirection: 'column',
						alignItems: 'center',
						gap: '16px',
						marginTop: '-20px',
					}}
				>
					{/* NeuralAgent Icon */}
					<div style={{ marginBottom: '8px' }}>
						<NeuralAgentIcon
							scale={iconScale}
							opacity={iconOpacity}
							glowIntensity={glowIntensity}
						/>
					</div>

					{/* Title: "NeuralAgent 3.0" */}
					<TypingText
						text="NeuralAgent 3.0"
						startFrame={TITLE_START}
						letterDuration={5}
						color="#e0e7ff"
						glowColor="#7c3aed"
						fontSize={52}
					/>

					{/* Subtitle */}
					<FadeInText
						text="你的 AI 桌面搭档"
						startFrame={SUBTITLE_START}
						fontSize={22}
						color="#a78bfa"
					/>
				</div>
			</AbsoluteFill>
		</AbsoluteFill>
	);
};
