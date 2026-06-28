import React from 'react';
import { FONT_FAMILY, FONT_WEIGHT } from '../../styles/typography';
import { usePulseAnimation } from '../hooks/usePulseAnimation';

export type BadgeVariant = 'loading' | 'loaded' | 'error' | 'one-off' | 'reusable';

export interface StatusBadgeProps {
  text: string;
  variant: BadgeVariant;
  size?: 'sm' | 'md' | 'lg';
}

const variantStyles: Record<BadgeVariant, { bg: string; color: string; pulse?: boolean }> = {
  loading: { bg: 'rgba(255,107,53,0.15)', color: '#FF6B35', pulse: true },
  loaded: { bg: 'rgba(46,213,115,0.15)', color: '#2ED573' },
  error: { bg: 'rgba(255,71,87,0.15)', color: '#FF4757' },
  'one-off': { bg: 'rgba(0,212,255,0.15)', color: '#00D4FF' },
  reusable: { bg: 'rgba(255,165,2,0.15)', color: '#FFA502' },
};

const sizeStyles = {
  sm: { fontSize: 11, padding: '3px 10px' },
  md: { fontSize: 12, padding: '4px 12px' },
  lg: { fontSize: 14, padding: '6px 16px' },
};

/**
 * Status indicator badge used in panels and lists.
 * Supports loading pulse animation and various color variants.
 */
export const StatusBadge: React.FC<StatusBadgeProps> = ({
  text,
  variant,
  size = 'sm',
}) => {
  const style = variantStyles[variant];
  const sizeStyle = sizeStyles[size];
  const pulse = usePulseAnimation({ intensity: style.pulse ? 0.6 : 0 });

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: FONT_FAMILY,
        fontWeight: FONT_WEIGHT.medium as number,
        color: style.color,
        backgroundColor: style.bg,
        padding: sizeStyle.padding,
        borderRadius: 999,
        fontSize: sizeStyle.fontSize,
        letterSpacing: 0.5,
        border: `1px solid ${style.color}${style.pulse ? Math.round(pulse.opacity * 100 + 40).toString(16).padStart(2, '0') : '40'}`,
      }}
    >
      {variant === 'loading' && (
        <span
          style={{
            width: 6,
            height: 6,
            borderRadius: '50%',
            backgroundColor: style.color,
            marginRight: 6,
            opacity: pulse.opacity,
          }}
        />
      )}
      {text}
    </span>
  );
};
