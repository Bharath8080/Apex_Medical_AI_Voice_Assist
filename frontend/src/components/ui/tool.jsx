import React, { useState } from 'react';
import { cn } from '../../lib/utils';
import { Database, Globe, CheckCircle2, Loader2, ChevronDown, Wrench } from 'lucide-react';

export function Tool({ toolPart = {}, defaultOpen = false, className }) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const { type = 'tool', state = 'output-available', input, output } = toolPart;

  const isRag = type.includes('rag');
  const isWeb = type.includes('web');
  const Icon = isRag ? Database : isWeb ? Globe : Wrench;

  const isStreaming = state === 'input-streaming';

  return (
    <div className={cn('w-full my-2 rounded-xl border border-white/10 bg-white/[0.03] overflow-hidden text-xs', className)}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-3 py-2 text-left hover:bg-white/[0.04] transition-colors cursor-pointer"
      >
        <div className="flex items-center gap-2">
          <Icon className={cn('w-4 h-4', isRag ? 'text-cyan-400' : isWeb ? 'text-emerald-400' : 'text-amber-400')} />
          <span className="font-mono font-semibold text-neutral-200">{type}</span>
          <span
            className={cn(
              'px-2 py-0.5 rounded-full text-[10px] font-medium flex items-center gap-1',
              isStreaming
                ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
            )}
          >
            {isStreaming ? (
              <>
                <Loader2 className="w-3 h-3 animate-spin" /> Calling...
              </>
            ) : (
              <>
                <CheckCircle2 className="w-3 h-3" /> Done
              </>
            )}
          </span>
        </div>
        <ChevronDown className={cn('w-4 h-4 text-neutral-400 transition-transform duration-200', isOpen && 'rotate-180')} />
      </button>

      {isOpen && (
        <div className="px-3 pb-3 pt-1 border-t border-white/5 space-y-2 font-mono text-[11px] bg-black/20">
          {input && (
            <div>
              <div className="text-neutral-400 uppercase text-[9px] tracking-wider mb-0.5">Input:</div>
              <div className="p-2 rounded bg-black/40 text-neutral-300 overflow-x-auto whitespace-pre-wrap">
                {typeof input === 'object' ? JSON.stringify(input, null, 2) : String(input)}
              </div>
            </div>
          )}
          {output && (
            <div>
              <div className="text-neutral-400 uppercase text-[9px] tracking-wider mb-0.5">Output:</div>
              <div className="p-2 rounded bg-black/40 text-neutral-300 max-h-40 overflow-y-auto whitespace-pre-wrap">
                {typeof output === 'object' ? JSON.stringify(output, null, 2) : String(output)}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
