import React from 'react';
import { cn } from '../../lib/utils';
import {
  Mic,
  MicOff,
  MessageSquareText,
  ChevronDown,
  PhoneCall,
  PhoneOff,
} from 'lucide-react';

/**
 * Official LiveKit Agents UI AgentControlBar component.
 * Features LiveKit's signature variant='livekit' pill dock styling with:
 * - Split capsule microphone track control + live VU meter
 * - Transcript toggle (MessageSquareText)
 * - AgentDisconnectButton (End Call / Start Call)
 */
export function AgentControlBar({
  variant = 'livekit', // 'livekit' | 'outline' | 'default'
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
        variant === 'livekit' ? 'rounded-[31px]' : 'rounded-xl',
        className
      )}
      {...props}
    >
      {/* Media Action Toggles */}
      <div className="flex items-center gap-1.5 sm:gap-2">
        {/* 1. LiveKit Microphone Split Control */}
        <div
          className={cn(
            'flex items-center rounded-full border transition-all duration-150',
            !isConnected
              ? 'bg-[#181a1f] border-[#252830] text-neutral-500 opacity-60'
              : isMuted
              ? 'bg-rose-950/40 border-rose-800/60 text-rose-300'
              : 'bg-[#1b1e24] border-[#292d37] hover:border-[#3d4352] text-neutral-200'
          )}
        >
          {/* Main Mic Toggle Button */}
          <button
            onClick={onToggleMute}
            disabled={!isConnected}
            aria-label="Toggle microphone"
            className="flex items-center gap-2 pl-3 pr-2 py-1.5 rounded-l-full hover:bg-white/5 transition-colors disabled:cursor-not-allowed"
          >
            {isMuted ? (
              <MicOff className="w-4 h-4 text-rose-400" />
            ) : (
              <Mic className="w-4 h-4 text-white" />
            )}

            {/* LiveKit Mini VU Meter */}
            <div className="flex items-end gap-[2px] h-3 px-0.5">
              {[8, 14, 8].map((maxH, i) => (
                <span
                  key={i}
                  className={cn(
                    'w-[2.5px] rounded-full transition-all duration-75',
                    isMuted || !isConnected
                      ? 'bg-neutral-600 h-[3px]'
                      : 'bg-white'
                  )}
                  style={{
                    height:
                      isConnected && !isMuted
                        ? `${Math.max(3, volume * maxH)}px`
                        : '3px',
                  }}
                />
              ))}
            </div>
          </button>

          {/* Dropdown Chevron Separator */}
          <button
            disabled={!isConnected}
            aria-label="Microphone device options"
            className="pr-2.5 pl-1 py-1.5 rounded-r-full hover:bg-white/5 text-neutral-400 hover:text-white transition-colors border-l border-[#292d37] disabled:cursor-not-allowed"
          >
            <ChevronDown className="w-3 h-3 opacity-70" />
          </button>
        </div>

        {/* 2. LiveKit Chat / Transcript Toggle */}
        <button
          onClick={() => onIsChatOpenChange && onIsChatOpenChange(!isChatOpen)}
          aria-label="Toggle transcript"
          className={cn(
            'p-2.5 rounded-full border transition-all duration-150',
            isChatOpen
              ? 'bg-neutral-700 text-white border-neutral-500 shadow-sm'
              : 'bg-[#181a1f] border-[#262932] hover:bg-[#20232a] text-neutral-400 hover:text-neutral-200'
          )}
          title="Toggle conversation transcript"
        >
          <MessageSquareText className="w-4 h-4" />
        </button>
      </div>

      {/* 3. LiveKit Signature Disconnect / Start Button */}
      <div>
        {!isConnected ? (
          <button
            onClick={onStart}
            aria-label="Start call session"
            className="flex items-center gap-2 px-4 sm:px-5 py-2 rounded-full bg-emerald-950/80 hover:bg-emerald-900 border border-emerald-700/70 text-emerald-300 font-outfit text-xs sm:text-sm font-bold tracking-wider uppercase shadow-lg transition-all hover:scale-105 active:scale-95 cursor-pointer"
          >
            <PhoneCall className="w-3.5 h-3.5 fill-current" />
            <span className="hidden sm:inline">Start Call</span>
            <span className="inline sm:hidden">Start</span>
          </button>
        ) : (
          <button
            onClick={onStop}
            aria-label="Disconnect agent session"
            className="flex items-center gap-2 px-4 sm:px-5 py-2 rounded-full bg-rose-950/60 hover:bg-rose-900/80 border border-rose-800/80 text-rose-300 font-outfit text-xs sm:text-sm font-bold tracking-wider uppercase shadow-lg transition-all hover:scale-105 active:scale-95 cursor-pointer"
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
