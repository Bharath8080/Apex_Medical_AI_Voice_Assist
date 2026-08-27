import { useState, useRef, useEffect, useCallback } from 'react';

const DEFAULT_WS_URL =
  import.meta.env.VITE_WS_URL ||
  (typeof window !== 'undefined'
    ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.hostname}:8000/ws`
    : 'ws://127.0.0.1:8000/ws');

export function useVoiceAgent(wsUrl = DEFAULT_WS_URL) {
  // Orb Lifecycle States: "idle" | "connecting" | "listening" | "thinking" | "speaking" | "error"
  const [orbState, setOrbState] = useState('idle');
  const [volume, setVolume] = useState(0);
  const [inputVolume, setInputVolume] = useState(0);
  const [outputVolume, setOutputVolume] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [messages, setMessages] = useState([]);
  const [errorMessage, setErrorMessage] = useState(null);

  // Audio & Connection Refs
  const wsRef = useRef(null);
  const audioCtxRef = useRef(null);
  const micStreamRef = useRef(null);
  const micSourceRef = useRef(null);
  const micProcessorRef = useRef(null);
  const micAnalyserRef = useRef(null);
  const botAnalyserRef = useRef(null);
  const nextPlayTimeRef = useRef(0);
  const activeSourcesRef = useRef(new Set());
  const isSpeakingRef = useRef(false);
  const animFrameRef = useRef(null);
  const smoothedInVolRef = useRef(0);
  const smoothedOutVolRef = useRef(0);

  // Stop currently playing/queued bot audio (used on interruption)
  const stopAudioPlayback = useCallback(() => {
    activeSourcesRef.current.forEach((src) => {
      try {
        src.stop();
        src.disconnect();
      } catch (e) {
        // ignore
      }
    });
    activeSourcesRef.current.clear();
    if (audioCtxRef.current) {
      nextPlayTimeRef.current = audioCtxRef.current.currentTime;
    }
    isSpeakingRef.current = false;
    smoothedOutVolRef.current = 0;
    setOutputVolume(0);
  }, []);

  // Real-time Volume Monitoring Loop (Calculates distinct inputVolume & outputVolume for orb-ui)
  const startVolumeLoop = useCallback(() => {
    const update = () => {
      let rawIn = 0;
      let rawOut = 0;

      // 1. Measure Mic Input Volume
      if (micAnalyserRef.current) {
        const inData = new Uint8Array(micAnalyserRef.current.frequencyBinCount);
        micAnalyserRef.current.getByteFrequencyData(inData);
        const sum = inData.reduce((acc, val) => acc + val, 0);
        const avg = sum / (inData.length || 1);
        rawIn = Math.min(1, (avg / 255) * 2.4);
      }

      // 2. Measure Bot Output Volume
      if (botAnalyserRef.current && isSpeakingRef.current) {
        const outData = new Uint8Array(botAnalyserRef.current.frequencyBinCount);
        botAnalyserRef.current.getByteFrequencyData(outData);
        const sum = outData.reduce((acc, val) => acc + val, 0);
        const avg = sum / (outData.length || 1);
        rawOut = Math.min(1, (avg / 255) * 2.6);
      }

      // Smooth volume interpolation (Attack/Release envelope)
      const inAttack = rawIn > smoothedInVolRef.current ? 0.45 : 0.2;
      const outAttack = rawOut > smoothedOutVolRef.current ? 0.5 : 0.25;

      smoothedInVolRef.current += (rawIn - smoothedInVolRef.current) * inAttack;
      smoothedOutVolRef.current += (rawOut - smoothedOutVolRef.current) * outAttack;

      const curIn = Number(smoothedInVolRef.current.toFixed(3));
      const curOut = Number(smoothedOutVolRef.current.toFixed(3));

      setInputVolume(curIn);
      setOutputVolume(curOut);
      setVolume(isSpeakingRef.current ? curOut : curIn);

      animFrameRef.current = requestAnimationFrame(update);
    };

    animFrameRef.current = requestAnimationFrame(update);
  }, []);

  const stopVolumeLoop = useCallback(() => {
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = null;
    }
  }, []);

  // Stop Call & Cleanup
  const stopCall = useCallback(() => {
    stopVolumeLoop();
    stopAudioPlayback();

    if (wsRef.current) {
      try {
        wsRef.current.close();
      } catch (e) {
        // ignore
      }
      wsRef.current = null;
    }

    if (micStreamRef.current) {
      micStreamRef.current.getTracks().forEach((t) => t.stop());
      micStreamRef.current = null;
    }

    if (micProcessorRef.current) {
      micProcessorRef.current.disconnect();
      micProcessorRef.current = null;
    }

    if (audioCtxRef.current) {
      try {
        audioCtxRef.current.close();
      } catch (e) {
        // ignore
      }
      audioCtxRef.current = null;
    }

    isSpeakingRef.current = false;
    smoothedInVolRef.current = 0;
    smoothedOutVolRef.current = 0;
    setInputVolume(0);
    setOutputVolume(0);
    setVolume(0);
    setOrbState('idle');
  }, [stopVolumeLoop, stopAudioPlayback]);

  // Start Call & Connect
  const startCall = useCallback(async () => {
    stopCall();
    setErrorMessage(null);
    setOrbState('connecting');

    try {
      // 1. Initialize Web Audio Context at 16kHz
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      const ctx = new AudioContextClass({ sampleRate: 16000 });
      audioCtxRef.current = ctx;
      await ctx.resume();

      // 2. Analysers for volume measurement
      const micAnalyser = ctx.createAnalyser();
      micAnalyser.fftSize = 64;
      micAnalyser.smoothingTimeConstant = 0.4;
      micAnalyserRef.current = micAnalyser;

      const botAnalyser = ctx.createAnalyser();
      botAnalyser.fftSize = 64;
      botAnalyser.smoothingTimeConstant = 0.4;
      botAnalyserRef.current = botAnalyser;

      // 3. Microphone Access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      micStreamRef.current = stream;

      const source = ctx.createMediaStreamSource(stream);
      micSourceRef.current = source;
      source.connect(micAnalyser);

      // 4. WebSocket Connection
      const ws = new WebSocket(wsUrl);
      ws.binaryType = 'arraybuffer';
      wsRef.current = ws;

      ws.onopen = () => {
        setOrbState('listening');
        nextPlayTimeRef.current = ctx.currentTime;
        startVolumeLoop();
      };

      ws.onclose = () => {
        stopCall();
      };

      ws.onerror = (err) => {
        console.error('WebSocket Error:', err);
        setErrorMessage('Failed to connect to voice server.');
        setOrbState('error');
      };

      // 5. Incoming Audio Playback & Transcripts
      ws.onmessage = async (event) => {
        if (event.data instanceof ArrayBuffer) {
          // Binary Audio PCM 16kHz mono
          if (ctx.state === 'suspended') {
            await ctx.resume();
          }

          const int16Array = new Int16Array(event.data);
          if (int16Array.length === 0) return;

          const float32Array = new Float32Array(int16Array.length);
          for (let i = 0; i < int16Array.length; i++) {
            float32Array[i] = int16Array[i] / 32768.0;
          }

          const audioBuffer = ctx.createBuffer(1, float32Array.length, 24000);
          audioBuffer.getChannelData(0).set(float32Array);

          const bufferSource = ctx.createBufferSource();
          bufferSource.buffer = audioBuffer;

          // Connect buffer -> botAnalyser -> destination
          bufferSource.connect(botAnalyser);
          botAnalyser.connect(ctx.destination);

          const currentTime = ctx.currentTime;
          if (nextPlayTimeRef.current < currentTime) {
            nextPlayTimeRef.current = currentTime;
          }

          bufferSource.start(nextPlayTimeRef.current);
          nextPlayTimeRef.current += audioBuffer.duration;

          activeSourcesRef.current.add(bufferSource);
          isSpeakingRef.current = true;
          setOrbState('speaking');

          bufferSource.onended = () => {
            activeSourcesRef.current.delete(bufferSource);
            if (activeSourcesRef.current.size === 0) {
              isSpeakingRef.current = false;
              setOrbState((prev) => (prev === 'speaking' ? 'listening' : prev));
            }
          };
        } else if (typeof event.data === 'string') {
          // JSON Transcripts & State Signals
          try {
            const data = JSON.parse(event.data);

            if (data.type === 'bot_state') {
              if (data.state === 'speaking') {
                isSpeakingRef.current = true;
                setOrbState('speaking');
              } else if (data.state === 'thinking') {
                stopAudioPlayback();
                setOrbState('thinking');
              } else if (data.state === 'listening') {
                if (activeSourcesRef.current.size === 0) {
                  isSpeakingRef.current = false;
                  setOrbState('listening');
                }
              }
            } else if (data.type === 'user_transcript') {
              if (data.final) {
                stopAudioPlayback();
                setOrbState('thinking');
              } else {
                setOrbState('listening');
              }

              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last && last.role === 'user' && !last.final) {
                  updated[updated.length - 1] = {
                    role: 'user',
                    text: data.text,
                    final: data.final,
                  };
                } else {
                  updated.push({
                    role: 'user',
                    text: data.text,
                    final: data.final,
                  });
                }
                return updated;
              });
            } else if (data.type === 'bot_transcript') {
              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last && last.role === 'bot') {
                  updated[updated.length - 1] = {
                    role: 'bot',
                    text: last.text + data.text,
                  };
                } else {
                  updated.push({ role: 'bot', text: data.text });
                }
                return updated;
              });
            }
          } catch (e) {
            console.error('Failed to parse text message:', event.data);
          }
        }
      };

      // 6. Mic PCM Streaming to Backend
      const processor = ctx.createScriptProcessor(4096, 1, 1);
      micProcessorRef.current = processor;

      processor.onaudioprocess = (e) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
        const inputData = e.inputBuffer.getChannelData(0);

        // Convert Float32 to Int16 PCM
        const pcm16 = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
          const s = Math.max(-1, Math.min(1, inputData[i]));
          pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
        }

        wsRef.current.send(pcm16.buffer);
      };

      // Echo prevention: route processor output into a muted gain node
      const muteGain = ctx.createGain();
      muteGain.gain.setValueAtTime(0, ctx.currentTime);
      source.connect(processor);
      processor.connect(muteGain);
      muteGain.connect(ctx.destination);
    } catch (err) {
      console.error('Failed to start voice agent:', err);
      setErrorMessage(err.message || 'Microphone or connection failed.');
      setOrbState('error');
      stopCall();
    }
  }, [wsUrl, startVolumeLoop, stopCall, stopAudioPlayback]);

  // Toggle Microphone Mute
  const toggleMute = useCallback(() => {
    if (micStreamRef.current) {
      const audioTracks = micStreamRef.current.getAudioTracks();
      if (audioTracks.length > 0) {
        const nextMuted = !isMuted;
        audioTracks[0].enabled = !nextMuted;
        setIsMuted(nextMuted);
      }
    }
  }, [isMuted]);

  useEffect(() => {
    return () => {
      stopCall();
    };
  }, [stopCall]);

  // Send Text Message to Agent
  const sendMessage = useCallback((text) => {
    if (!text || !text.trim()) return;
    const trimmed = text.trim();

    stopAudioPlayback();
    setOrbState('thinking');

    // Send plain string over WebSocket to Pipecat
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(trimmed);
    }
  }, [stopAudioPlayback]);

  return {
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
    clearMessages: () => setMessages([]),
  };
}
