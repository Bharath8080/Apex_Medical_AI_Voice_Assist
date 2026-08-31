import React from 'react';
import { cn } from '../../lib/utils';
import {
  Mic,
  MicOff,
  MessageSquareText,
  PhoneCall,
  PhoneOff,
} from 'lucide-react';

/**
 * Modern AgentControlBar with enlarged boundary and perfectly contained VU meter wave animation.
 */
export function AgentControlBar({
  variant = 'livekit',
  state = 'idle',
  isMuted = false,
  volume = 0,
  isChatOpen = false,
  onIsChatOpenChange,
  onStart,
  onStop,
  onToggleMute,
  className,
  ...props
}) {
  const isConnected = state !== 'idle' && state !== 'error';

  return (
    <div
      aria-label="Voice assistant controls"
      className={cn(
        'bg-[#121417]/95 border border-[#20232a] text-neutral-100 shadow-2xl backdrop-blur-2xl flex items-center justify-between gap-3 sm:gap-6 p-2 sm:p-2.5 select-none transition-all',
        variant === 'livekit' ? 'rounded-[32px]' : 'rounded-xl',
        className
      )}
      {...props}
    >
      {/* Media Action Toggles */}
      <div className="flex items-center gap-2 sm:gap-2.5">
        {/* Enlarged Microphone Control Pill with Contained Waves */}
        <button
          onClick={onToggleMute}
          disabled={!isConnected}
          aria-label="Toggle microphone"
          title={!isConnected ? "Start call first" : isMuted ? "Unmute microphone" : "Mute microphone"}
          className={cn(
            'flex items-center gap-2.5 px-3.5 sm:px-4 py-2 sm:py-2.5 rounded-full border transition-all duration-150 cursor-pointer disabled:cursor-not-allowed',
            !isConnected
              ? 'bg-[#181a1f] border-[#252830] text-neutral-500 opacity-60'
              : isMuted
              ? 'bg-rose-950/40 border-rose-800/60 text-rose-300 hover:bg-rose-900/50'
              : 'bg-[#1b1e24] border-[#292d37] hover:border-[#3d4352] text-neutral-200 hover:bg-[#22262e]'
          )}
        >
          {isMuted ? (
            <MicOff className="w-4 h-4 text-rose-400 shrink-0" />
          ) : (
            <Mic className="w-4 h-4 text-white shrink-0" />
          )}

          {/* Enclosed Mini VU Meter (Container size strictly contains dynamic wave heights) */}
          <div className="flex items-center gap-[3px] h-4 px-1 rounded-md bg-black/20 overflow-hidden">
            {[6, 12, 6].map((maxH, i) => (
              <span
                key={i}
                className={cn(
                  'w-[3px] rounded-full transition-all duration-75 origin-center',
                  isMuted || !isConnected
                    ? 'bg-neutral-600 h-[3px]'
                    : 'bg-emerald-400'
                )}
                style={{
                  height:
                    isConnected && !isMuted
                      ? `${Math.min(12, Math.max(3, volume * maxH))}px`
                      : '3px',
                }}
              />
            ))}
          </div>
        </button>

        {/* Transcript Toggle */}
        <button
          onClick={() => onIsChatOpenChange && onIsChatOpenChange(!isChatOpen)}
          aria-label="Toggle transcript"
          className={cn(
            'p-2.5 sm:p-3 rounded-full border transition-all duration-150 cursor-pointer',
            isChatOpen
              ? 'bg-neutral-700 text-white border-neutral-500 shadow-sm'
              : 'bg-[#181a1f] border-[#262932] hover:bg-[#20232a] text-neutral-400 hover:text-neutral-200'
          )}
          title="Toggle conversation transcript"
        >
          <MessageSquareText className="w-4 h-4" />
        </button>
      </div>

      {/* Disconnect / Start Button */}
      <div>
        {!isConnected ? (
          <button
            onClick={onStart}
            aria-label="Start call session"
            className="flex items-center gap-2 px-4 sm:px-5 py-2.5 rounded-full bg-emerald-950/80 hover:bg-emerald-900 border border-emerald-700/70 text-emerald-300 font-outfit text-xs sm:text-sm font-bold tracking-wider uppercase shadow-lg transition-all hover:scale-105 active:scale-95 cursor-pointer"
          >
            <PhoneCall className="w-3.5 h-3.5 fill-current" />
            <span className="hidden sm:inline">Start Call</span>
            <span className="inline sm:hidden">Start</span>
          </button>
        ) : (
          <button
            onClick={onStop}
            aria-label="Disconnect agent session"
            className="flex items-center gap-2 px-4 sm:px-5 py-2.5 rounded-full bg-rose-950/60 hover:bg-rose-900/80 border border-rose-800/80 text-rose-300 font-outfit text-xs sm:text-sm font-bold tracking-wider uppercase shadow-lg transition-all hover:scale-105 active:scale-95 cursor-pointer"
          >
            <PhoneOff className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">End Call</span>
            <span className="inline sm:hidden">End</span>
          </button>
        )}
      </div>
    </div>
  );
}
