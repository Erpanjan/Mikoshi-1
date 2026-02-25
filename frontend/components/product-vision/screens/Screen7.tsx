import React, { useMemo } from 'react';
import { Phone, Play, Video, FileText, Mic } from 'lucide-react';
import { useScreenTranslation } from '../hooks/useScreenTranslation';
import { ScreenContainer } from '../shared/ScreenContainer';
import type { VoiceConnectionStatus } from '@/lib/voice-agent/types';

interface Screen7Props {
  onCallAgent?: () => void;
  voiceStatus: VoiceConnectionStatus;
  voiceError: string | null;
  isVoiceMuted: boolean;
  onStartVoiceSession: () => void;
  onEndVoiceSession: () => void;
  onToggleMute: () => void;
}

export const Screen7 = ({
  onCallAgent,
  voiceStatus,
  voiceError,
  isVoiceMuted,
  onStartVoiceSession,
  onEndVoiceSession,
  onToggleMute,
}: Screen7Props) => {
  const t = useScreenTranslation('screen7');
  const isConnected = voiceStatus === 'connected';
  const isConnecting = voiceStatus === 'connecting';

  const chatHistory = useMemo(() => [
    { id: 1, type: "system", text: t.chat.system1 },
    {
      id: 2,
      type: "agent",
      text: t.chat.agent1,
      attachment: "video",
    },
    { id: 3, type: "system", text: t.chat.system2 },
    {
      id: 4,
      type: "agent",
      text: t.chat.agent2,
    },
    {
      id: 5,
      type: "agent",
      text: t.chat.agent3,
      attachment: "action",
    },
  ], [t]);

  return (
    <ScreenContainer>
      <div className="pt-20 pb-4 border-b border-gray-100 flex items-end justify-between px-6 bg-white shrink-0 dark:bg-black dark:border-white/10 transition-colors duration-300">
        <div>
          <h2 className="text-xl font-sans font-medium text-onyx dark:text-white transition-colors duration-300">
            AI Companion
          </h2>
          {voiceError && (
            <p className="mt-1 text-[10px] font-mono text-red-600 dark:text-red-400">{voiceError}</p>
          )}
        </div>
        <button
          onClick={() => {
            if (isConnected || isConnecting) {
              onEndVoiceSession();
              return;
            }
            onStartVoiceSession();
            onCallAgent?.();
          }}
          className="w-10 h-10 border border-gray-200 flex items-center justify-center rounded-full bg-white hover:bg-black hover:border-black transition-colors group relative mb-1 dark:bg-[#3B3B3D] dark:border-white/10 dark:hover:bg-white dark:hover:text-onyx"
        >
          <Phone
            size={16}
            className="text-onyx group-hover:text-white transition-colors dark:text-white dark:group-hover:text-onyx"
          />
          <div className="absolute -top-1 -right-1 w-2 h-2 bg-red-600 rounded-full animate-pulse dark:bg-red-400"></div>
        </button>
      </div>
      <div className="flex-1 overflow-y-auto scrollbar-hide p-6 space-y-8">
        {chatHistory.map((msg) => {
          if (msg.type === "system")
            return (
              <div key={msg.id} className="flex items-center gap-4">
                <div className="h-px flex-1 bg-gray-200 dark:bg-white/10"></div>
                <span className="text-[9px] font-mono text-gray-400 uppercase tracking-widest dark:text-[#A3A3A3]">
                  {msg.text}
                </span>
                <div className="h-px flex-1 bg-gray-200 dark:bg-white/10"></div>
              </div>
            );
          return (
            <div key={msg.id} className="flex gap-4">
              <div className="w-6 pt-1 text-right shrink-0">
                <span className="text-[9px] font-mono font-bold text-onyx uppercase dark:text-white">
                  AI
                </span>
              </div>
              <div className="flex-1 max-w-[90%]">
                <div className="bg-white border border-gray-200 p-4 rounded-2xl rounded-tl-sm text-xs text-onyx leading-relaxed shadow-sm dark:bg-[#3B3B3D] dark:border-white/5 dark:text-[#E6E6E7] transition-colors duration-300">
                  {msg.text}
                </div>
                {msg.attachment === "video" && (
                  <div className="mt-2 bg-[#FAFAFA] border border-gray-200 p-3 flex gap-4 items-center group cursor-pointer hover:border-black transition-colors rounded-xl dark:bg-[#2A2A2A] dark:border-white/5 dark:hover:border-white">
                    <div className="w-10 h-10 bg-white border border-gray-200 flex items-center justify-center shrink-0 rounded-lg dark:bg-[#3B3B3D] dark:border-white/5">
                      <Play size={16} className="text-onyx fill-onyx dark:text-white dark:fill-white" />
                    </div>
                    <div>
                      <div className="text-[10px] font-bold text-onyx uppercase tracking-wide dark:text-white">
                        {t.chat.pitch}
                      </div>
                      <div className="text-[9px] text-gray-400 font-mono mt-0.5 dark:text-[#A3A3A3]">
                        24 MIN • 14 NOV
                      </div>
                    </div>
                  </div>
                )}
                {msg.attachment === "action" && (
                  <div className="mt-4 space-y-2">
                    <div className="flex gap-2">
                      <button className="flex-1 bg-white border border-gray-200 py-3 text-[10px] font-bold text-onyx uppercase hover:bg-gray-50 flex items-center justify-center gap-2 transition-colors rounded-xl dark:bg-[#3B3B3D] dark:border-white/5 dark:text-white dark:hover:bg-[#4A4A4D]">
                        <Video size={12} /> {t.chat.buttons.explain}
                      </button>
                      <button className="flex-1 bg-white border border-gray-200 py-3 text-[10px] font-bold text-onyx uppercase hover:bg-gray-50 flex items-center justify-center gap-2 transition-colors rounded-xl dark:bg-[#3B3B3D] dark:border-white/5 dark:text-white dark:hover:bg-[#4A4A4D]">
                        <FileText size={12} /> {t.chat.buttons.report}
                      </button>
                    </div>
                    <button className="w-full bg-onyx text-white py-4 text-[10px] font-bold uppercase tracking-[0.2em] hover:bg-black transition-colors rounded-xl dark:bg-white dark:text-onyx dark:hover:bg-white">
                      {t.chat.buttons.review}
                    </button>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
      <div className="p-4 border-t border-gray-100 bg-white dark:bg-black dark:border-white/10 transition-colors duration-300">
        <div className="h-12 border border-gray-200 bg-white flex items-center px-4 justify-between text-gray-400 hover:border-gray-400 transition-colors rounded-xl dark:bg-[#3B3B3D] dark:border-white/5 dark:text-[#A3A3A3] dark:hover:border-white/20">
          <span className="text-xs uppercase tracking-wider font-bold text-gray-300 dark:text-[#A3A3A3]">
            {isConnected ? (isVoiceMuted ? 'Mic muted' : 'Mic live') : 'Ask the AI Companion'}
          </span>
          <button
            type="button"
            onClick={onToggleMute}
            disabled={!isConnected}
            className="disabled:opacity-40 disabled:cursor-not-allowed"
            aria-label={isVoiceMuted ? 'Unmute microphone' : 'Mute microphone'}
          >
            <Mic size={16} className="text-onyx dark:text-white" />
          </button>
        </div>
      </div>
    </ScreenContainer>
  );
};
