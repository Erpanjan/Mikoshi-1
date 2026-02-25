import React from 'react';
import { Layers } from 'lucide-react';
import { useScreenTranslation } from '../hooks/useScreenTranslation';
import { ScreenContainer } from '../shared/ScreenContainer';
import { PrimaryButton } from '../shared/PrimaryButton';
import type { PolicyMenu } from '@/lib/policy/types';

const summarizeMenuText = (text: string): string => {
  const cleaned = text.trim().replace(/\s+/g, ' ');
  if (!cleaned) {
    return '';
  }
  const firstSentenceEnd = cleaned.search(/[.!?]/);
  const firstSentence = firstSentenceEnd > 40 ? cleaned.slice(0, firstSentenceEnd + 1) : cleaned;
  const maxChars = 180;
  return firstSentence.length > maxChars ? `${firstSentence.slice(0, maxChars - 1)}...` : firstSentence;
};

const summaryFontClass = (text: string): string => {
  const length = text.length;
  if (length > 210) return 'text-[11px]';
  if (length > 160) return 'text-xs';
  if (length > 110) return 'text-[13px]';
  return 'text-sm';
};

export const Screen4 = ({
  onAnalyzeDepth,
  menu,
  proposalIndex,
  proposalCount,
}: {
  onAnalyzeDepth?: () => void;
  menu: PolicyMenu;
  proposalIndex: number;
  proposalCount: number;
}) => {
  const t = useScreenTranslation('screen4');
  const displayIndex = String(Math.max(1, proposalIndex)).padStart(2, '0');
  const displayCount = String(Math.max(1, proposalCount)).padStart(2, '0');
  const menuSummary = summarizeMenuText(menu.summary || t.description);
  const summaryClass = summaryFontClass(menuSummary);

  return (
    <ScreenContainer>
      <div className="pt-20 px-6 pb-6 border-b border-gray-100 flex justify-between items-end dark:border-white/10">
        <div>
          <h2 className="text-3xl font-sans font-medium text-onyx dark:text-white transition-colors duration-300">{t.header}</h2>
          <div className="flex items-center gap-2 mt-2">
            <span className="text-[10px] font-bold text-onyx uppercase tracking-widest dark:text-white">
              {`Proposal ${displayIndex}`}
            </span>
            <span className="w-8 h-px bg-gray-300 dark:bg-gray-600"></span>
            <span className="text-[10px] font-mono text-gray-400 uppercase dark:text-[#A3A3A3]">
              {displayCount}
            </span>
          </div>
        </div>
        <Layers size={20} className="text-onyx dark:text-white" />
      </div>

      <div className="flex-1 px-6 py-6 flex items-center justify-center relative overflow-hidden bg-[#FAFAFA] dark:bg-black transition-colors duration-300">
        <div className="absolute right-[-10%] top-[15%] bottom-[15%] w-[20%] border-l border-gray-200 opacity-40 z-0 dark:border-white/10"></div>

        <div className="w-full h-full bg-white border border-gray-200 shadow-xl shadow-gray-200/50 flex flex-col relative z-10 rounded-2xl overflow-hidden dark:bg-[#3B3B3D] dark:border-white/5 dark:shadow-none transition-colors duration-300">
          <div className="p-8 pb-0 shrink-0">
            <h3 className="text-3xl font-sans font-medium text-onyx leading-[1.1] mb-2 dark:text-white transition-colors duration-300">
              {menu.title || t.title}
            </h3>
          </div>

          <div className="p-8 pt-4 flex-1 flex flex-col justify-start overflow-hidden">
            <p
              className={`${summaryClass} text-gray-500 leading-relaxed font-sans border-l-2 border-onyx pl-4 mb-4 dark:text-[#E6E6E7] dark:border-white transition-colors duration-300`}
            >
              {menuSummary}
            </p>
          </div>

          <div className="p-6 pt-0 border-t border-transparent">
            <PrimaryButton
              className="h-14 shadow-lg"
              showArrow={true}
              onClick={onAnalyzeDepth}
            >
              {t.button}
            </PrimaryButton>
          </div>
        </div>
      </div>

      <div className="flex justify-center gap-3 pb-6 bg-[#FAFAFA] dark:bg-black transition-colors duration-300">
        <div className="w-2 h-2 bg-onyx rounded-full dark:bg-white" title={`Proposal ${displayIndex}`} />
        <div className="w-2 h-2 border border-gray-300 rounded-full dark:border-gray-700"></div>
        <div className="w-2 h-2 border border-gray-300 rounded-full dark:border-gray-700"></div>
      </div>
    </ScreenContainer>
  );
};
