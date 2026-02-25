'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { MessagePayload } from '@elevenlabs/types';

import { ConsultationVoiceAgent } from '@/lib/voice-agent/consultation-agent';
import type {
  ConsultationTranscriptTurn,
  VoiceConnectionStatus,
  VoiceConversationMode,
  VoiceDisconnectReason,
} from '@/lib/voice-agent/types';

const toTranscriptTurn = (message: MessagePayload): ConsultationTranscriptTurn => ({
  id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
  role: message.role,
  message: message.message,
  timestamp: Date.now(),
});

export function useConsultationVoiceAgent() {
  const agentRef = useRef<ConsultationVoiceAgent | null>(null);
  if (!agentRef.current) {
    agentRef.current = new ConsultationVoiceAgent();
  }

  const [status, setStatus] = useState<VoiceConnectionStatus>('idle');
  const [error, setError] = useState<string | null>(null);
  const [isMuted, setIsMuted] = useState(false);
  const [transcript, setTranscript] = useState<ConsultationTranscriptTurn[]>([]);
  const [disconnectReason, setDisconnectReason] = useState<VoiceDisconnectReason>(null);
  const [mode, setMode] = useState<VoiceConversationMode>(null);
  const [inputVolume, setInputVolume] = useState(0);
  const [outputVolume, setOutputVolume] = useState(0);

  const startSession = useCallback(async () => {
    if (status === 'connecting' || status === 'connected') {
      return;
    }

    setError(null);
    setDisconnectReason(null);
    setMode(null);
    setStatus('connecting');

    try {
      await agentRef.current?.start({
        onStatusChange: setStatus,
        onMessage: (message) => {
          setTranscript((prev) => [...prev, toTranscriptTurn(message)]);
        },
        onError: (message) => {
          setError(message);
          setStatus('error');
        },
        onDisconnect: (details) => {
          const reason = details?.reason;
          if (reason === 'agent' || reason === 'user' || reason === 'error') {
            setDisconnectReason(reason);
          } else {
            setDisconnectReason(null);
          }
        },
        onModeChange: (nextMode) => {
          setMode(nextMode);
        },
      });
      setStatus('connected');
      setIsMuted(false);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to start consultation voice session';
      setError(message);
      setStatus('error');
    }
  }, [status]);

  const prewarmSession = useCallback(async () => {
    if (status === 'connected' || status === 'connecting') {
      return;
    }
    try {
      await agentRef.current?.prefetchSession();
    } catch {
      // Best-effort optimization only; ignore failures and keep normal start flow.
    }
  }, [status]);

  const endSession = useCallback(async () => {
    try {
      setStatus('disconnecting');
      setDisconnectReason('user');
      await agentRef.current?.stop();
      setStatus('idle');
      setIsMuted(false);
      setMode(null);
      setInputVolume(0);
      setOutputVolume(0);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to stop consultation voice session';
      setError(message);
      setStatus('error');
    }
  }, []);

  const toggleMute = useCallback(async () => {
    if (status !== 'connected') {
      return;
    }

    const nextMuted = await agentRef.current?.toggleMute();
    if (typeof nextMuted === 'boolean') {
      setIsMuted(nextMuted);
    }
  }, [status]);

  const clearTranscript = useCallback(() => {
    setTranscript([]);
    setDisconnectReason(null);
  }, []);

  useEffect(() => {
    if (status !== 'connected') {
      setInputVolume(0);
      setOutputVolume(0);
      return;
    }

    const intervalId = window.setInterval(() => {
      const agent = agentRef.current;
      if (!agent) {
        return;
      }

      const nextInput = Number.isFinite(agent.getInputVolume()) ? agent.getInputVolume() : 0;
      const nextOutput = Number.isFinite(agent.getOutputVolume()) ? agent.getOutputVolume() : 0;
      setInputVolume(Math.max(0, Math.min(1, nextInput)));
      setOutputVolume(Math.max(0, Math.min(1, nextOutput)));
    }, 80);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [status]);

  useEffect(() => {
    return () => {
      const agent = agentRef.current;
      if (agent) {
        void agent.stop();
      }
    };
  }, []);

  return useMemo(
    () => ({
      status,
      error,
      isMuted,
      transcript,
      disconnectReason,
      mode,
      inputVolume,
      outputVolume,
      startSession,
      prewarmSession,
      endSession,
      toggleMute,
      clearTranscript,
    }),
    [
      status,
      error,
      isMuted,
      transcript,
      disconnectReason,
      mode,
      inputVolume,
      outputVolume,
      startSession,
      prewarmSession,
      endSession,
      toggleMute,
      clearTranscript,
    ]
  );
}
