import React from 'react';

interface BoomerangCanvasProps {
  className?: string;
  intensity?: 'subtle' | 'medium';
}

export const BoomerangCanvas: React.FC<BoomerangCanvasProps> = ({
  className = '',
  intensity = 'subtle'
}) => {
  const strokeColor = intensity === 'medium' ? 'rgba(25, 25, 25, 0.05)' : 'rgba(25, 25, 25, 0.03)';
  return (
    <div
      className={`pointer-events-none select-none absolute inset-0 w-full h-full overflow-hidden ${className}`}
      aria-hidden="true"
      style={{
        backgroundImage: `linear-gradient(to right, ${strokeColor} 1px, transparent 1px), linear-gradient(to bottom, ${strokeColor} 1px, transparent 1px)`,
        backgroundSize: '48px 48px'
      }}
    />
  );
};
