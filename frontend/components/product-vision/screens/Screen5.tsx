import React, { useEffect, useMemo, useRef, useState } from 'react';
import { List, Pause, Play } from 'lucide-react';

import { ScreenContainer } from '../shared/ScreenContainer';
import { PrimaryButton } from '../shared/PrimaryButton';
import type { PolicyDetail, PolicySecurity } from '@/lib/policy/types';

const formatPct = (value: number): string => `${Number(value || 0).toFixed(2)}%`;

const formatMoney = (currency: string, value: number): string => {
  const safeValue = Number.isFinite(value) ? value : 0;
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency || 'USD',
    maximumFractionDigits: 0,
  }).format(safeValue);
};

const groupByAssetClass = (securities: PolicySecurity[]): Record<string, PolicySecurity[]> => {
  return securities.reduce<Record<string, PolicySecurity[]>>((acc, row) => {
    const key = row.asset_class?.trim() || 'Other';
    if (!acc[key]) {
      acc[key] = [];
    }
    acc[key].push(row);
    return acc;
  }, {});
};

const isPortfolioSection = (title: string): boolean => {
  const normalized = title.trim().toLowerCase();
  return normalized === 'investment vehicle selection highlights';
};

const SecuritiesBlock = ({
  currency,
  groupedSecurities,
}: {
  currency: string;
  groupedSecurities: Record<string, PolicySecurity[]>;
}) => {
  if (Object.keys(groupedSecurities).length === 0) {
    return <p className="text-xs text-gray-500 dark:text-[#A3A3A3]">No securities returned.</p>;
  }

  return (
    <div className="space-y-5">
      {Object.entries(groupedSecurities).map(([assetClass, securities]) => (
        <div key={assetClass}>
          <h4 className="text-[11px] font-semibold text-onyx dark:text-white mb-2">{assetClass}</h4>
          <div className="space-y-2">
            {securities.map((security) => (
              <div
                key={`${assetClass}-${security.id}`}
                className="border border-gray-100 rounded-xl p-3 bg-gray-50 dark:bg-[#2A2A2A] dark:border-white/5"
              >
                <div className="text-[11px] font-semibold text-onyx dark:text-white">
                  {security.name || security.id}
                </div>
                <div className="mt-1 grid grid-cols-2 gap-2 text-[10px] text-gray-600 dark:text-[#A3A3A3]">
                  <span>Target allocation: {formatPct(security.allocation_pct)}</span>
                  <span>
                    Target amount: {formatMoney(currency, Number(security.allocation_amount || 0))}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export const Screen5 = ({
  onProceed,
  detail,
  onToggleVoiceExplanation,
  isVoicePlaying,
  voiceStatus,
  activeVoiceSectionKey,
}: {
  onProceed?: () => void;
  detail: PolicyDetail;
  onToggleVoiceExplanation: () => void;
  isVoicePlaying: boolean;
  voiceStatus: 'idle' | 'connecting' | 'connected' | 'disconnecting' | 'error';
  activeVoiceSectionKey?: string | null;
}) => {
  const sections = Array.isArray(detail.sections) ? detail.sections : [];
  const currency = detail.portfolio?.currency || 'USD';
  const [highlightedSectionKey, setHighlightedSectionKey] = useState<string | null>(null);
  const sectionRefs = useRef<Record<string, HTMLElement | null>>({});
  const userPauseUntilRef = useRef(0);
  const autoScrollLockRef = useRef(false);
  const highlightTimeoutRef = useRef<number | null>(null);

  const groupedSecurities = useMemo(
    () => groupByAssetClass(detail.portfolio?.securities || []),
    [detail.portfolio?.securities]
  );

  useEffect(() => {
    return () => {
      if (highlightTimeoutRef.current !== null) {
        window.clearTimeout(highlightTimeoutRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (!isVoicePlaying || !activeVoiceSectionKey) {
      return;
    }

    const targetElement = sectionRefs.current[activeVoiceSectionKey];
    if (!targetElement) {
      return;
    }

    const now = Date.now();
    if (now < userPauseUntilRef.current) {
      return;
    }

    autoScrollLockRef.current = true;
    targetElement.scrollIntoView({
      behavior: 'smooth',
      block: 'start',
      inline: 'nearest',
    });
    window.setTimeout(() => {
      autoScrollLockRef.current = false;
    }, 700);

    setHighlightedSectionKey(activeVoiceSectionKey);
    if (highlightTimeoutRef.current !== null) {
      window.clearTimeout(highlightTimeoutRef.current);
    }
    highlightTimeoutRef.current = window.setTimeout(() => {
      setHighlightedSectionKey((prev) => (prev === activeVoiceSectionKey ? null : prev));
    }, 2200);
  }, [activeVoiceSectionKey, isVoicePlaying]);

  const onManualScrollIntent = () => {
    if (!isVoicePlaying || autoScrollLockRef.current) {
      return;
    }
    userPauseUntilRef.current = Date.now() + 10000;
  };

  return (
    <ScreenContainer>
      <div className="pt-20 px-6 pb-4 border-b border-gray-100 bg-white shrink-0 dark:bg-black dark:border-white/10 transition-colors duration-300">
        <div className="flex items-center justify-between gap-4 mt-2">
          <h2 className="text-lg font-sans font-medium text-onyx dark:text-white transition-colors duration-300">
            {detail.title || 'Policy Breakdown'}
          </h2>
          <button
            type="button"
            onClick={onToggleVoiceExplanation}
            className="h-9 px-3 rounded-full border border-gray-200 bg-white hover:bg-gray-50 text-onyx text-[10px] font-semibold uppercase tracking-wider flex items-center gap-2 dark:bg-[#3B3B3D] dark:border-white/10 dark:text-white dark:hover:bg-[#4A4A4D] transition-colors"
            aria-label={isVoicePlaying ? 'Stop policy explanation' : 'Play policy explanation'}
          >
            {isVoicePlaying ? <Pause size={12} /> : <Play size={12} />}
            {isVoicePlaying ? 'Stop' : (voiceStatus === 'connecting' ? 'Starting' : 'Play')}
          </button>
        </div>
      </div>

      <div
        className="flex-1 overflow-y-auto scrollbar-hide p-6 space-y-6"
        onWheel={onManualScrollIntent}
        onTouchMove={onManualScrollIntent}
      >
        {sections.map((section) => (
          <section
            key={section.id}
            ref={(node) => {
              sectionRefs.current[section.id] = node;
            }}
            className={`bg-white border rounded-2xl p-4 shadow-sm dark:bg-[#3B3B3D] transition-colors duration-500 ${
              highlightedSectionKey === section.id
                ? 'border-gray-400 dark:border-white/40'
                : 'border-gray-100 dark:border-white/5'
            }`}
          >
            <h3 className="text-xs font-bold uppercase tracking-widest text-onyx dark:text-white mb-3 flex items-center gap-2">
              <List size={12} />
              {isPortfolioSection(section.title) ? 'Recommended Investment Portfolio' : section.title}
            </h3>
            {isPortfolioSection(section.title) ? (
              <SecuritiesBlock currency={currency} groupedSecurities={groupedSecurities} />
            ) : (
              <p className="text-xs leading-relaxed text-gray-600 whitespace-pre-wrap dark:text-[#E6E6E7]">
                {section.content}
              </p>
            )}
          </section>
        ))}

        <div className="pt-2 pb-8">
          <PrimaryButton onClick={onProceed} showArrow={true}>
            Proceed to Execution
          </PrimaryButton>
        </div>
      </div>
    </ScreenContainer>
  );
};
