import React, { useState } from 'react';
import { cn } from '../../lib/utils';
import { Database, Globe, Calendar, CheckCircle2, Loader2, ChevronDown, Wrench } from 'lucide-react';

const TOOL_CONFIG = {
  rag_search: {
    label: 'Apex Hospital Knowledge Base',
    icon: Database,
    color: 'text-cyan-400',
    border: 'border-cyan-500/30 bg-cyan-950/20',
  },
  web_search: {
    label: 'Live Web Search',
    icon: Globe,
    color: 'text-emerald-400',
    border: 'border-emerald-500/30 bg-emerald-950/20',
  },
  check_available_slots: {
    label: 'Doctor Slot Availability',
    icon: Calendar,
    color: 'text-amber-400',
    border: 'border-amber-500/30 bg-amber-950/20',
  },
  book_appointment: {
    label: 'Cal.com Appointment Booking',
    icon: Calendar,
    color: 'text-purple-400',
    border: 'border-purple-500/30 bg-purple-950/20',
  },
};

export function Tool({ toolPart = {}, defaultOpen = false, className }) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const { type = 'tool', state = 'output-available', input, output } = toolPart;

  const config = TOOL_CONFIG[type] || {
    label: type,
    icon: Wrench,
    color: 'text-neutral-300',
    border: 'border-white/10 bg-white/[0.04]',
  };
  const Icon = config.icon;
  const isStreaming = state === 'input-streaming';

  return (
    <div className={cn('w-full my-2 rounded-xl border overflow-hidden text-xs shadow-sm select-none', config.border, className)}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-3.5 py-2.5 text-left hover:bg-white/[0.04] transition-colors cursor-pointer"
      >
        <div className="flex items-center gap-2.5 min-w-0">
          <Icon className={cn('w-4 h-4 shrink-0', config.color)} />
          <span className="font-outfit text-xs font-semibold text-neutral-200 truncate">
            {config.label}
          </span>
          <span
            className={cn(
              'px-2 py-0.5 rounded-full text-[10px] font-medium font-outfit flex items-center gap-1 shrink-0',
              isStreaming
                ? 'bg-blue-500/20 text-blue-300 border border-blue-500/40 animate-pulse'
                : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
            )}
          >
            {isStreaming ? (
              <>
                <Loader2 className="w-3 h-3 animate-spin text-blue-300" />
                <span>Calling...</span>
              </>
            ) : (
              <>
                <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                <span>Done</span>
              </>
            )}
          </span>
        </div>

        <ChevronDown className={cn('w-4 h-4 text-neutral-400 transition-transform duration-200 shrink-0', isOpen && 'rotate-180')} />
      </button>

      {isOpen && (
        <div className="px-3.5 pb-3 pt-1 border-t border-white/10 space-y-2 font-mono text-[11px] bg-black/40">
          {input !== undefined && input !== null && (
            <div>
              <div className="text-neutral-400 uppercase text-[9px] font-outfit font-bold tracking-wider mb-1">
                Input Parameters:
              </div>
              <div className="p-2 rounded-lg bg-black/60 text-neutral-300 overflow-x-auto whitespace-pre-wrap border border-white/5">
                {typeof input === 'object' ? JSON.stringify(input, null, 2) : String(input)}
              </div>
            </div>
          )}

          {output !== undefined && output !== null && output !== '' && (
            <div>
              <div className="text-neutral-400 uppercase text-[9px] font-outfit font-bold tracking-wider mb-1">
                Tool Output:
              </div>
              <div className="p-2 rounded-lg bg-black/60 text-neutral-300 max-h-48 overflow-y-auto whitespace-pre-wrap border border-white/5">
                {typeof output === 'object' ? JSON.stringify(output, null, 2) : String(output)}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
