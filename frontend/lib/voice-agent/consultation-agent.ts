import type { Conversation } from '@elevenlabs/client';

import { fetchConsultationSignedUrl, startConsultationConversation } from './client';
import type { ConsultationSessionInit, ConsultationVoiceCallbacks, ConsultationVoiceSession } from './types';

export class ConsultationVoiceAgent {
  private conversation: Conversation | null = null;
  private session: ConsultationSessionInit | null = null;
  private prefetchedSession: ConsultationSessionInit | null = null;
  private prefetchedAt: number | null = null;
  private muted = false;
  private static readonly PREFETCH_TTL_MS = 45_000;

  public getSession(): ConsultationVoiceSession | null {
    if (!this.conversation || !this.session) {
      return null;
    }

    return {
      conversation: this.conversation,
      agentId: this.session.agentId,
      signedUrl: this.session.signedUrl,
    };
  }

  public isMuted(): boolean {
    return this.muted;
  }

  public async start(callbacks: ConsultationVoiceCallbacks): Promise<ConsultationVoiceSession> {
    if (this.conversation && this.session) {
      return {
        conversation: this.conversation,
        agentId: this.session.agentId,
        signedUrl: this.session.signedUrl,
      };
    }

    const now = Date.now();
    const hasFreshPrefetch = Boolean(
      this.prefetchedSession &&
      this.prefetchedAt !== null &&
      now - this.prefetchedAt <= ConsultationVoiceAgent.PREFETCH_TTL_MS
    );

    const prefetchedSession = hasFreshPrefetch ? this.prefetchedSession : null;
    let started;
    try {
      started = await startConsultationConversation(callbacks, prefetchedSession);
    } catch (error) {
      if (!prefetchedSession) {
        throw error;
      }
      started = await startConsultationConversation(callbacks, null);
    }
    const { conversation, session } = started;
    this.conversation = conversation;
    this.session = session;
    this.prefetchedSession = null;
    this.prefetchedAt = null;
    this.muted = false;

    return {
      conversation,
      agentId: session.agentId,
      signedUrl: session.signedUrl,
    };
  }

  public async stop(): Promise<void> {
    if (!this.conversation) {
      return;
    }

    await this.conversation.endSession();
    this.conversation = null;
    this.session = null;
    this.muted = false;
  }

  public async prefetchSession(): Promise<void> {
    if (this.conversation) {
      return;
    }

    const now = Date.now();
    const hasFreshPrefetch = Boolean(
      this.prefetchedSession &&
      this.prefetchedAt !== null &&
      now - this.prefetchedAt <= ConsultationVoiceAgent.PREFETCH_TTL_MS
    );
    if (hasFreshPrefetch) {
      return;
    }

    const session = await fetchConsultationSignedUrl();
    this.prefetchedSession = session;
    this.prefetchedAt = Date.now();
  }

  public setMuted(muted: boolean): void {
    if (!this.conversation) {
      this.muted = muted;
      return;
    }

    this.conversation.setMicMuted(muted);
    this.muted = muted;
  }

  public async toggleMute(): Promise<boolean> {
    const nextMuted = !this.muted;
    this.setMuted(nextMuted);
    return nextMuted;
  }

  public getInputVolume(): number {
    if (!this.conversation) {
      return 0;
    }
    return this.conversation.getInputVolume();
  }

  public getOutputVolume(): number {
    if (!this.conversation) {
      return 0;
    }
    return this.conversation.getOutputVolume();
  }
}
