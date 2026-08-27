import React, { useState } from 'react';
import { useVoiceAgent } from './hooks/useVoiceAgent';
import { Orb } from './components/ui/orb';
import { ShimmeringText } from './components/ui/shimmering-text';
import { AgentControlBar } from './components/agents-ui/agent-control-bar';
import { AgentChatTranscript } from './components/agents-ui/agent-chat-transcript';

const STATUS_CONFIG = {
  idle: {
    text: 'Press Start Call to begin conversation',
    color: '#94a3b8',
    shimmerColor: '#ffffff',
    showDots: false,
  },
  connecting: {
    text: 'Connecting to agent',
    color: '#38bdf8',
    shimmerColor: '#ffffff',
    showDots: true,
  },
  listening: {
    text: 'Agent is listening, ask it a question',
    color: '#34d399',
    shimmerColor: '#ffffff',
    showDots: true,
  },
  thinking: {
    text: 'Agent is processing',
    color: '#fbbf24',
    shimmerColor: '#ffffff',
    showDots: true,
  },
  speaking: {
    text: 'Agent is speaking',
    color: '#22d3ee',
    shimmerColor: '#ffffff',
    showDots: true,
  },
  error: {
    text: 'Connection error. Please try again.',
    color: '#f87171',
    shimmerColor: '#ffffff',
    showDots: false,
  },
};

const ORB_COLOR_PRESETS = [
  {
    id: 'blue',
    label: 'Sky Blue',
    colors: ['#CADCFC', '#A0B9D1'],
    accent: '#A0B9D1',
  },
  {
    id: 'sand',
    label: 'Warm Sand',
    colors: ['#EAD2B8', '#D1AB84'],
    accent: '#D1AB84',
  },
  {
    id: 'silver',
    label: 'Silver Gray',
    colors: ['#E2E8F0', '#94A3B8'],
    accent: '#94A3B8',
  },
  {
    id: 'cyan',
    label: 'Cyber Cyan',
    colors: ['#22d3ee', '#818cf8'],
    accent: '#22d3ee',
  },
];

export function App() {
  const {
    orbState,
    volume,
    inputVolume,
    outputVolume,
    isMuted,
    messages,
    errorMessage,
    startCall,
    stopCall,
    toggleMute,
    sendMessage,
    clearMessages,
  } = useVoiceAgent();

  const [themeId, setThemeId] = useState('blue');
  const [isChatOpen, setIsChatOpen] = useState(false);

  const currentTheme =
    ORB_COLOR_PRESETS.find((t) => t.id === themeId) || ORB_COLOR_PRESETS[0];

  return (
    <div className="w-full h-[100dvh] bg-[#07080a] text-neutral-100 flex flex-col justify-between font-sans select-none overflow-hidden">
      {/* 1. LiveKit Header */}
      <header className="h-14 px-4 sm:px-6 flex items-center justify-between border-b border-white/10 shrink-0 bg-[#0a0c0f]">
        <div className="flex items-center gap-3">
          <div className="w-6 h-6 rounded-md bg-white/10 border border-white/20 flex items-center justify-center text-white font-outfit font-bold text-xs">
            LK
          </div>
          <span className="font-outfit text-xs sm:text-sm font-bold tracking-wider text-neutral-200 uppercase">
            LiveKit Voice RAG
          </span>
        </div>

        {/* Header Actions */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Color Preset Palette Picker */}
          <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-white/5 border border-white/10">
            {ORB_COLOR_PRESETS.map((preset) => (
              <button
                key={preset.id}
                onClick={() => setThemeId(preset.id)}
                title={`Color theme: ${preset.label}`}
                className={`w-5 h-5 rounded-full transition-all duration-150 relative cursor-pointer ${
                  themeId === preset.id
                    ? 'ring-2 ring-white ring-offset-2 ring-offset-[#0a0c0f] scale-110'
                    : 'opacity-60 hover:opacity-100 hover:scale-105'
                }`}
                style={{
                  background: `linear-gradient(135deg, ${preset.colors[0]}, ${preset.colors[1]})`,
                }}
              />
            ))}
          </div>
        </div>
      </header>

      {/* Error Notification */}
      {errorMessage && (
        <div className="w-fit mx-auto mt-2 px-4 py-1 rounded-lg bg-rose-950/90 border border-rose-800 text-rose-300 text-xs shadow-lg z-20 shrink-0 font-outfit font-medium">
          {errorMessage}
        </div>
      )}

      {/* 2. Main Stage with LiveKit Tile System */}
      <main className="flex-1 flex flex-col md:flex-row items-stretch justify-center p-3 sm:p-5 gap-4 min-h-0 relative overflow-hidden">
        {/* Assistant Tile */}
        <div className="flex-1 flex flex-col justify-between items-center rounded-2xl bg-[#0c0e12]/80 border border-white/10 p-4 sm:p-6 min-h-0 relative overflow-hidden">
          {/* Tile Header Label */}
          <div className="w-full flex items-center justify-between shrink-0 font-outfit text-xs sm:text-sm tracking-wider text-neutral-400 font-bold uppercase">
            <span>ASSISTANT</span>
            <span className="flex items-center gap-1.5">
              <span
                className={`w-2 h-2 rounded-full ${
                  orbState === 'speaking'
                    ? 'bg-cyan-400 animate-ping'
                    : orbState === 'listening'
                    ? 'bg-emerald-400'
                    : orbState === 'thinking'
                    ? 'bg-amber-400 animate-pulse'
                    : 'bg-neutral-600'
                }`}
              />
              <span className="text-neutral-300 font-bold">{orbState.toUpperCase()}</span>
            </span>
          </div>

          {/* Visualizer Hero Area (Dedicated 3D Orb) */}
          <div className="flex-1 w-full flex flex-col items-center justify-center min-h-0 my-auto">
            <div className="w-64 h-64 sm:w-80 sm:h-80 flex items-center justify-center relative">
              <Orb
                agentState={
                  orbState === 'speaking'
                    ? 'talking'
                    : orbState === 'listening'
                    ? 'listening'
                    : orbState === 'thinking'
                    ? 'thinking'
                    : null
                }
                volumeMode="manual"
                manualInput={inputVolume}
                manualOutput={outputVolume}
                colors={currentTheme.colors}
                className="w-full h-full"
              />
            </div>

            {/* Subtitle status with Fluid ShimmeringText Animation */}
            {(() => {
              const currentStatus = STATUS_CONFIG[orbState] || STATUS_CONFIG.idle;
              return (
                <div className="mt-8 sm:mt-10 text-center min-h-[36px] flex items-center justify-center">
                  <ShimmeringText
                    text={currentStatus.text}
                    className="font-outfit text-sm sm:text-base md:text-lg font-bold tracking-normal drop-shadow-sm"
                    color={currentStatus.color}
                    shimmerColor={currentStatus.shimmerColor}
                    showDots={currentStatus.showDots}
                    duration={4.0}
                  />
                </div>
              );
            })()}
          </div>

          {/* Bottom LiveKit Control Dock */}
          <div className="w-full flex items-center justify-center shrink-0 pt-2">
            <AgentControlBar
              variant="livekit"
              state={orbState}
              isMuted={isMuted}
              volume={volume}
              isChatOpen={isChatOpen}
              onIsChatOpenChange={setIsChatOpen}
              onStart={startCall}
              onStop={stopCall}
              onToggleMute={toggleMute}
            />
          </div>
        </div>

        {/* Conversation Drawer / Tile */}
        {isChatOpen && (
          <div className="w-full md:w-[380px] lg:w-[420px] h-[340px] md:h-full shrink-0 animate-in fade-in zoom-in-95 duration-200 min-w-0 overflow-hidden">
            <AgentChatTranscript
              messages={messages}
              onSendMessage={sendMessage}
              onClear={clearMessages}
              onClose={() => setIsChatOpen(false)}
              className="w-full h-full"
            />
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
