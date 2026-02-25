'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Conversation } from '@elevenlabs/client';
import type { MessagePayload } from '@elevenlabs/types';

import type {
  ConsultationSessionInit,
  ConsultationSignedUrlResponse,
  VoiceConversationMode,
  VoiceConnectionStatus,
  VoiceDisconnectReason,
} from '@/lib/voice-agent/types';

const POLICY_SESSION_ENDPOINT = '/api/voice-agent/policy/session';

const mapElevenLabsStatus = (status: string): VoiceConnectionStatus => {
  if (status === 'connected') return 'connected';
  if (status === 'connecting') return 'connecting';
  if (status === 'disconnecting') return 'disconnecting';
  return 'idle';
};

const fetchPolicySignedUrl = async (): Promise<ConsultationSessionInit> => {
  const response = await fetch(POLICY_SESSION_ENDPOINT, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  const payload = (await response.json()) as ConsultationSignedUrlResponse;
  if (!response.ok || !payload.success || !payload.signed_url || !payload.agent_id) {
    throw new Error(payload.error || `Failed to create policy voice session (${response.status})`);
  }

  return {
    signedUrl: payload.signed_url,
    agentId: payload.agent_id,
  };
};

export function usePolicyExplanationVoiceAgent() {
  const conversationRef = useRef<Conversation | null>(null);

  const [status, setStatus] = useState<VoiceConnectionStatus>('idle');
  const [error, setError] = useState<string | null>(null);
  const [disconnectReason, setDisconnectReason] = useState<VoiceDisconnectReason>(null);
  const [mode, setMode] = useState<VoiceConversationMode>(null);
  const [inputVolume, setInputVolume] = useState(0);
  const [outputVolume, setOutputVolume] = useState(0);
  const [lastAgentMessage, setLastAgentMessage] = useState('');
  const [activeSectionKey, setActiveSectionKey] = useState<string | null>(null);

  const start = useCallback(async (policyContext: string, orderedSections: Array<{ id: string; title: string }> = []) => {
    if (conversationRef.current || status === 'connecting' || status === 'connected') {
      return;
    }

    setError(null);
    setDisconnectReason(null);
    setMode(null);
    setLastAgentMessage('');
    setActiveSectionKey(null);
    setStatus('connecting');

    try {
      const session = await fetchPolicySignedUrl();
      const conversation = await Conversation.startSession({
        signedUrl: session.signedUrl,
        onStatusChange: ({ status: nextStatus }) => {
          setStatus(mapElevenLabsStatus(nextStatus));
        },
        onDisconnect: (details) => {
          const reason = details?.reason;
          if (reason === 'agent' || reason === 'user' || reason === 'error') {
            setDisconnectReason(reason);
          } else {
            setDisconnectReason(null);
          }
          conversationRef.current = null;
          setStatus('idle');
        },
        onMessage: (message: MessagePayload) => {
          if (message.role !== 'agent') {
            return;
          }
          const text = message.message || '';
          setLastAgentMessage(text);
          const sectionMatch = text.match(/\[\[SECTION:([a-zA-Z0-9_-]+)\]\]/i);
          if (sectionMatch?.[1]) {
            setActiveSectionKey(sectionMatch[1].trim());
          }
        },
        onModeChange: ({ mode: nextMode }) => {
          setMode(nextMode ?? null);
        },
        onError: (message) => {
          setError(message);
          setStatus('error');
        },
      });

      conversationRef.current = conversation;
      setStatus('connected');

      const normalizedContext = (policyContext || '').trim();
      if (normalizedContext) {
        conversation.sendContextualUpdate(normalizedContext);
      }
      const orderedSectionPrompt = orderedSections.length
        ? orderedSections.map((section, index) => `${index + 1}. ${section.id} :: ${section.title}`).join('\n')
        : '';
      conversation.sendUserMessage(
        [
          'You are in client Q&A mode for policy discussion.',
          'Do not start with a full policy walkthrough unless the client explicitly asks for a full walkthrough.',
          'Start with one short question asking what the client wants to discuss first.',
          'When answering a client question tied to a specific policy section, prefix your response with a machine tag in this exact format: [[SECTION:<section_id>]].',
          'If multiple sections are relevant, choose the primary section first and use one section tag per response.',
          orderedSectionPrompt ? `Use only these section IDs/titles as valid references:\n${orderedSectionPrompt}` : '',
          'Keep answers concise, advisory, and conversational.',
        ]
          .filter(Boolean)
          .join('\n\n')
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start policy voice explanation');
      setStatus('error');
    }
  }, [status]);

  const stop = useCallback(async () => {
    const conversation = conversationRef.current;
    if (!conversation) {
      setStatus('idle');
      return;
    }

    setStatus('disconnecting');
    setDisconnectReason('user');
    setMode(null);
    setActiveSectionKey(null);
    try {
      await conversation.endSession();
    } finally {
      conversationRef.current = null;
      setStatus('idle');
    }
  }, []);

  useEffect(() => {
    if (status !== 'connected') {
      setInputVolume(0);
      setOutputVolume(0);
      return;
    }

    const intervalId = window.setInterval(() => {
      const conversation = conversationRef.current;
      if (!conversation) {
        return;
      }

      const nextInput = Number.isFinite(conversation.getInputVolume()) ? conversation.getInputVolume() : 0;
      const nextOutput = Number.isFinite(conversation.getOutputVolume()) ? conversation.getOutputVolume() : 0;
      setInputVolume(Math.max(0, Math.min(1, nextInput)));
      setOutputVolume(Math.max(0, Math.min(1, nextOutput)));
    }, 80);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [status]);

  return useMemo(
    () => ({
      status,
      error,
      disconnectReason,
      mode,
      inputVolume,
      outputVolume,
      lastAgentMessage,
      activeSectionKey,
      isPlaying: status === 'connected' || status === 'connecting',
      start,
      stop,
    }),
    [status, error, disconnectReason, mode, inputVolume, outputVolume, lastAgentMessage, activeSectionKey, start, stop]
  );
}
