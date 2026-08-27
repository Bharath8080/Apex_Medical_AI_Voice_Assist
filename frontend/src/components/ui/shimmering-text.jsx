'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../../lib/utils';

export function ShimmeringText({
  text,
  duration = 4.0,
  className,
  color = '#cbd5e1',
  shimmerColor = '#ffffff',
  showDots = true,
}) {
  // Ultra-smooth 110deg continuous sweeping light bar
  const gradientStyle = `linear-gradient(110deg, ${color} 0%, ${color} 35%, ${shimmerColor} 50%, ${color} 65%, ${color} 100%)`;

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={text}
        initial={{ opacity: 0, y: 5 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -5 }}
        transition={{ duration: 0.3 }}
        className={cn('inline-flex items-center justify-center select-none', className)}
      >
        {/* Sweeping Shimmer Text */}
        <motion.span
          className="inline-block bg-[length:200%_100%] bg-clip-text text-transparent"
          style={{
            backgroundImage: gradientStyle,
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
          animate={{
            backgroundPosition: ['200% center', '-200% center'],
          }}
          transition={{
            repeat: Infinity,
            duration: duration,
            ease: 'linear',
          }}
        >
          {text}
        </motion.span>

        {/* Pulsing Motion Dots Animation at the end (...) - aligned slightly down */}
        {showDots && (
          <span className="inline-flex items-center gap-[4px] ml-2 translate-y-[2px]">
            {[0, 1, 2].map((i) => (
              <motion.span
                key={i}
                className="w-1.5 h-1.5 rounded-full inline-block"
                style={{ backgroundColor: shimmerColor }}
                animate={{
                  scale: [0.75, 1.25, 0.75],
                  opacity: [0.25, 1, 0.25],
                }}
                transition={{
                  duration: 1.6,
                  repeat: Infinity,
                  delay: i * 0.25,
                  ease: 'easeInOut',
                }}
              />
            ))}
          </span>
        )}
      </motion.div>
    </AnimatePresence>
  );
}

export default ShimmeringText;
