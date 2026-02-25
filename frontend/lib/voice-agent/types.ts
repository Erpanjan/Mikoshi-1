import type { Conversation, Status } from '@elevenlabs/client';
import type { MessagePayload } from '@elevenlabs/types';

export type VoiceConnectionStatus = 'idle' | 'connecting' | 'connected' | 'disconnecting' | 'error';
export type VoiceDisconnectReason = 'agent' | 'user' | 'error' | null;
export type VoiceConversationMode = 'speaking' | 'listening' | null;

export interface VoiceDisconnectDetails {
  reason?: VoiceDisconnectReason | string;
  message?: string;
}

export interface ConsultationSignedUrlResponse {
  success: boolean;
  signed_url?: string;
  agent_id?: string;
  error?: string;
  details?: unknown;
}

export interface ConsultationSessionInit {
  signedUrl: string;
  agentId: string;
}

export interface ConsultationTranscriptTurn {
  id: string;
  role: MessagePayload['role'];
  message: string;
  timestamp: number;
}

export interface ConsultationVoiceCallbacks {
  onStatusChange?: (status: VoiceConnectionStatus) => void;
  onMessage?: (message: MessagePayload) => void;
  onError?: (message: string) => void;
  onDisconnect?: (details: VoiceDisconnectDetails) => void;
  onModeChange?: (mode: VoiceConversationMode) => void;
}

export interface ConsultationVoiceSession {
  conversation: Conversation;
  agentId: string;
  signedUrl: string;
}

export type ElevenLabsStatus = Status;
