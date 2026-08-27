'use client';

import React, { memo } from 'react';
import { Streamdown } from 'streamdown';
import { cn } from '../../lib/utils';

export const Response = memo(function Response({
  children,
  className,
  ...props
}) {
  return (
    <Streamdown
      className={cn(
        'prose prose-invert max-w-none text-xs sm:text-sm leading-relaxed [&>*:first-child]:mt-0 [&>*:last-child]:mb-0 select-text',
        className
      )}
      mode="streaming"
      animated={true}
      {...props}
    >
      {typeof children === 'string' ? children : String(children || '')}
    </Streamdown>
  );
});

export default Response;
