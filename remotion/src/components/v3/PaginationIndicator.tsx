import React from 'react';
import { ThemePalette } from '../../themes';

export interface PaginationIndicatorProps {
  total: number;
  current: number;
  theme: ThemePalette;
  position?: 'bottom' | 'right';
}

/**
 * Pagination dots indicator used in panels.
 * Shows current page/tab/section in a series of dots.
 */
export const PaginationIndicator: React.FC<PaginationIndicatorProps> = ({
  total,
  current,
  theme,
  position = 'bottom',
}) => {
  const isVertical = position === 'right';

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: isVertical ? 'column' : 'row',
        gap: 8,
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {Array.from({ length: total }, (_, i) => {
        const isActive = i === current;
        return (
          <div
            key={i}
            style={{
              width: isActive ? 24 : 8,
              height: 8,
              borderRadius: 4,
              backgroundColor: isActive
                ? theme.accentOrange ?? '#FF6B35'
                : 'rgba(255,255,255,0.2)',
              transition: 'all 0.3s ease',
            }}
          />
        );
      })}
    </div>
  );
};
