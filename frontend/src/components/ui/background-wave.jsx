import React from 'react';
import { cn } from '../../lib/utils';

export function BackgroundWave({
  className,
  colors = ['#CADCFC', '#A0B9D1'],
}) {
  const primaryColor = colors[0] || '#22d3ee';
  const secondaryColor = colors[1] || '#818cf8';

  return (
    <div className={cn('absolute inset-0 pointer-events-none overflow-hidden z-0 select-none', className)}>
      {/* 1. Inverted & Grayscale Luminous 3D Silk Wave Video */}
      <video
        src="/wave-loop.mp4"
        autoPlay
        muted
        loop
        playsInline
        controls={false}
        className="w-full h-full object-cover pointer-events-none mix-blend-screen opacity-70 contrast-125 brightness-100 filter invert grayscale"
      />

      {/* 2. Color tinting layer matching Orb colors */}
      <div
        className="absolute inset-0 pointer-events-none transition-all duration-700 mix-blend-color opacity-75"
        style={{
          background: `linear-gradient(135deg, ${primaryColor} 0%, ${secondaryColor} 100%)`,
        }}
      />

      {/* 3. Vignette Edge Fades */}
      <div className="absolute inset-0 bg-gradient-to-t from-[#07080a] via-transparent to-[#07080a]/80 pointer-events-none" />
      <div className="absolute inset-0 bg-gradient-to-r from-[#07080a]/90 via-transparent to-[#07080a]/90 pointer-events-none" />

      {/* 4. Ambient Glow Matching Theme */}
      <div
        className="absolute inset-0 pointer-events-none transition-all duration-700 mix-blend-screen opacity-35"
        style={{
          background: `radial-gradient(ellipse at 50% 50%, ${primaryColor} 0%, transparent 65%)`,
        }}
      />
    </div>
  );
}
