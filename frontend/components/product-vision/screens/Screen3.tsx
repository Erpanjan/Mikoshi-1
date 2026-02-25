import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Keyboard, X } from 'lucide-react';
import { CircularAudioWaveform } from '../shared/CircularAudioWaveform';
import { useScreenTranslation } from '../hooks/useScreenTranslation';
import { ScreenContainer } from '../shared/ScreenContainer';
import type {
  ConsultationTranscriptTurn,
  VoiceConnectionStatus,
  VoiceConversationMode,
  VoiceDisconnectReason,
} from '@/lib/voice-agent/types';

const QUESTION_HINTS = [
  'what',
  'how',
  'when',
  'where',
  'why',
  'which',
  'who',
  'can you',
  'could you',
  'would you',
  'do you',
  'are you',
  'is there',
];

const extractQuestionText = (text: string): string => {
  const normalized = text
    .replace(/\[[^\]]*\]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  if (!normalized) {
    return '';
  }

  const lower = normalized.toLowerCase();

  // Find the first question opener and cut preamble before it.
  const startIndexes = QUESTION_HINTS.map((hint) => lower.indexOf(hint)).filter((idx) => idx >= 0);
  const questionStart = startIndexes.length ? Math.min(...startIndexes) : -1;
  const candidate = questionStart >= 0 ? normalized.slice(questionStart).trim() : normalized;

  // If sentence has an explicit question mark, cut to that boundary.
  const questionMarkIndex = candidate.indexOf('?');
  if (questionMarkIndex >= 0) {
    return candidate.slice(0, questionMarkIndex + 1).trim();
  }

  // Fallback for streaming/incomplete punctuation: keep only if it starts with a question opener.
  const candidateLower = candidate.toLowerCase();
  const looksLikeQuestion = QUESTION_HINTS.some((hint) => candidateLower.startsWith(hint));
  return looksLikeQuestion ? candidate : '';
};

const summarizePrompt = (text: string): string => {
  const questionText = extractQuestionText(text);
  if (!questionText) {
    return '';
  }

  const maxLength = 72;
  return questionText.length > maxLength ? `${questionText.slice(0, maxLength - 1)}...` : questionText;
};

const promptClassName = (text: string): string => {
  const length = text.length;
  if (length > 95) {
    return 'text-[22px]';
  }
  if (length > 70) {
    return 'text-[26px]';
  }
  return 'text-3xl';
};

export const Screen3 = ({
  onSwitchToChat,
  onConsultationEnd,
  isDarkMode,
  voiceStatus,
  voiceMode,
  voiceError,
  voiceIsMuted,
  voiceInputVolume,
  voiceOutputVolume,
  voiceTranscript,
  voiceDisconnectReason,
  onStartVoiceSession,
  onEndVoiceSession,
  onToggleVoiceMute,
  onResetVoiceTranscript,
}: {
  onSwitchToChat: () => void;
  onConsultationEnd?: (reason: 'agent' | 'user') => void;
  isDarkMode?: boolean;
  voiceStatus: VoiceConnectionStatus;
  voiceMode: VoiceConversationMode;
  voiceError: string | null;
  voiceIsMuted: boolean;
  voiceInputVolume: number;
  voiceOutputVolume: number;
  voiceTranscript: ConsultationTranscriptTurn[];
  voiceDisconnectReason: VoiceDisconnectReason;
  onStartVoiceSession: () => void;
  onEndVoiceSession: () => Promise<void>;
  onToggleVoiceMute: () => Promise<void>;
  onResetVoiceTranscript: () => void;
}) => {
  const t = useScreenTranslation('screen3');
  const [sessionStarted, setSessionStarted] = useState(false);
  const [isNavigatingAfterEnd, setIsNavigatingAfterEnd] = useState(false);

  const latestAgentPrompt = useMemo(() => {
    const latestAgentMessage = [...voiceTranscript].reverse().find((turn) => turn.role === 'agent')?.message ?? '';
    return summarizePrompt(latestAgentMessage);
  }, [voiceTranscript]);

  const statusLabel = useMemo(() => {
    if (!sessionStarted && voiceStatus === 'idle') {
      return 'Start Session';
    }
    if (voiceStatus === 'connecting') {
      return 'Starting';
    }
    if (voiceStatus === 'disconnecting') {
      return 'Ending';
    }
    if (voiceStatus === 'error') {
      return 'Retry';
    }
    if (voiceStatus === 'connected' && voiceIsMuted) {
      return t.status.resume;
    }
    if (voiceStatus === 'connected' && voiceMode === 'speaking') {
      return t.status.speaking;
    }
    return t.status.listening;
  }, [sessionStarted, voiceStatus, voiceIsMuted, voiceMode, t]);

  const waveLevel = useMemo(() => {
    if (voiceStatus !== 'connected' || voiceIsMuted) {
      return 0;
    }
    return voiceMode === 'speaking' ? voiceOutputVolume : voiceInputVolume;
  }, [voiceStatus, voiceIsMuted, voiceMode, voiceOutputVolume, voiceInputVolume]);

  const handleCircleTap = useCallback(async () => {
    if (voiceStatus === 'connecting' || voiceStatus === 'disconnecting') {
      return;
    }

    if (!sessionStarted || voiceStatus === 'idle' || voiceStatus === 'error') {
      setSessionStarted(true);
      onStartVoiceSession();
      return;
    }

    await onToggleVoiceMute();
  }, [voiceStatus, sessionStarted, onStartVoiceSession, onToggleVoiceMute]);

  const handleForceEnd = useCallback(async () => {
    setIsNavigatingAfterEnd(true);
    await onEndVoiceSession();
    onConsultationEnd?.('user');
  }, [onConsultationEnd, onEndVoiceSession]);

  useEffect(() => {
    void onEndVoiceSession();
    onResetVoiceTranscript();
    setSessionStarted(false);
    setIsNavigatingAfterEnd(false);
  }, [onEndVoiceSession, onResetVoiceTranscript]);

  useEffect(() => {
    if (!sessionStarted || isNavigatingAfterEnd) {
      return;
    }
    if (voiceDisconnectReason === 'agent') {
      onConsultationEnd?.('agent');
    }
  }, [sessionStarted, isNavigatingAfterEnd, voiceDisconnectReason, onConsultationEnd]);

  return (
    <ScreenContainer className="justify-between overflow-hidden relative">
      <div className="pt-24 px-8 z-10">
        <div className="w-12 h-[2px] bg-onyx mb-6 dark:bg-white transition-colors duration-300"></div>
        <div className="min-h-[108px]">
          {latestAgentPrompt ? (
            <h2
              className={`${promptClassName(latestAgentPrompt)} font-sans font-medium text-onyx leading-[1.1] tracking-tight dark:text-white transition-colors duration-300`}
            >
              {latestAgentPrompt}
            </h2>
          ) : null}
        </div>
        {voiceError ? (
          <p className="mt-3 text-[11px] font-mono text-red-600 dark:text-red-400">{voiceError}</p>
        ) : null}
      </div>

      <div className="flex-1 flex flex-col items-center justify-center relative">
        <div
          className="relative w-64 h-64 flex items-center justify-center border border-gray-100 rounded-full dark:border-white/10 transition-colors duration-300"
        >
          <CircularAudioWaveform
            isPaused={voiceStatus === 'idle' || voiceStatus === 'error'}
            level={waveLevel}
            size={256}
            color={(voiceStatus !== 'connected' || voiceIsMuted)
              ? (isDarkMode ? "#333" : "#E5E5E5")
              : (isDarkMode ? "#FFFFFF" : "#3B3B3D")}
            onClick={() => {
              void handleCircleTap();
            }}
          />

          <span className={`absolute pointer-events-none text-[10px] font-bold uppercase tracking-[0.2em] z-10 transition-colors ${(voiceStatus !== 'connected' || voiceIsMuted) ? "text-onyx dark:text-[#A3A3A3]" : "text-white dark:text-onyx"
            }`}>
            {statusLabel}
          </span>
        </div>
      </div>

      <div className="pb-12 px-8 flex justify-between items-center w-full z-10 relative">
        <button
          onClick={() => {
            void handleForceEnd();
          }}
          disabled={voiceStatus === 'disconnecting'}
          className="p-4 rounded-full bg-gray-50 hover:bg-gray-100 dark:bg-[#3B3B3D] dark:hover:bg-white dark:hover:text-onyx transition-all duration-300 group"
          aria-label="End session"
        >
          <X
            size={24}
            className="text-onyx dark:text-white group-hover:scale-110 transition-transform duration-300 dark:group-hover:text-onyx"
            strokeWidth={1.5}
          />
        </button>

        <button
          onClick={() => {
            void onEndVoiceSession();
            onSwitchToChat();
          }}
          className="p-4 rounded-full bg-gray-50 hover:bg-gray-100 dark:bg-[#3B3B3D] dark:hover:bg-white dark:hover:text-onyx transition-all duration-300 group"
          aria-label="Switch to chat"
        >
          <Keyboard
            size={24}
            className="text-onyx dark:text-white group-hover:scale-110 transition-transform duration-300 dark:group-hover:text-onyx"
            strokeWidth={1.5}
          />
        </button>
      </div>
    </ScreenContainer>
  );
};
