import { Conversation } from '@elevenlabs/client';
import type { MessagePayload } from '@elevenlabs/types';

import type {
  ConsultationSessionInit,
  ConsultationSignedUrlResponse,
  ConsultationVoiceCallbacks,
  VoiceConnectionStatus,
} from './types';

const CONSULTATION_SESSION_ENDPOINT = '/api/voice-agent/consultation/session';

const mapElevenLabsStatus = (status: string): VoiceConnectionStatus => {
  if (status === 'connected') return 'connected';
  if (status === 'connecting') return 'connecting';
  if (status === 'disconnecting') return 'disconnecting';
  return 'idle';
};

export async function fetchConsultationSignedUrl(): Promise<ConsultationSessionInit> {
  const response = await fetch(CONSULTATION_SESSION_ENDPOINT, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  const payload = (await response.json()) as ConsultationSignedUrlResponse;
  if (!response.ok || !payload.success || !payload.signed_url || !payload.agent_id) {
    const message = payload.error ?? `Failed to create voice session (${response.status})`;
    throw new Error(message);
  }

  return {
    signedUrl: payload.signed_url,
    agentId: payload.agent_id,
  };
}

export async function startConsultationConversation(
  callbacks: ConsultationVoiceCallbacks,
  prefetchedSession?: ConsultationSessionInit | null
): Promise<{
  conversation: Conversation;
  session: ConsultationSessionInit;
}> {
  const session = prefetchedSession ?? (await fetchConsultationSignedUrl());

  const conversation = await Conversation.startSession({
    signedUrl: session.signedUrl,
    onStatusChange: ({ status }) => {
      callbacks.onStatusChange?.(mapElevenLabsStatus(status));
    },
    onMessage: (message: MessagePayload) => {
      callbacks.onMessage?.(message);
    },
    onModeChange: ({ mode }) => {
      callbacks.onModeChange?.(mode ?? null);
    },
    onError: (message: string) => {
      callbacks.onStatusChange?.('error');
      callbacks.onError?.(message);
    },
    onDisconnect: (details) => {
      callbacks.onDisconnect?.(details ?? {});
      callbacks.onStatusChange?.('idle');
    },
  });

  return { conversation, session };
}
