import React, { useMemo, useState } from 'react';
import { AlertTriangle } from 'lucide-react';

import { useScreenTranslation } from '../hooks/useScreenTranslation';
import { ScreenContainer } from '../shared/ScreenContainer';
import { PrimaryButton } from '../shared/PrimaryButton';
import type { FinancialDiagnosisCard } from '@/lib/policy/types';

interface ScreenFinancialDiagnosesProps {
  diagnoses: FinancialDiagnosisCard[];
  onNext?: () => void;
}

export const ScreenFinancialDiagnoses = ({
  diagnoses,
  onNext,
}: ScreenFinancialDiagnosesProps) => {
  const t = useScreenTranslation('screenFinancialDiagnoses');
  const cards = useMemo(() => {
    if (Array.isArray(diagnoses) && diagnoses.length > 0) {
      return diagnoses;
    }
    return [
      {
        id: 'placeholder-1',
        category: 'investment related' as const,
        title: t.emptyStateTitle,
        description: t.emptyStateDescription,
      },
    ];
  }, [diagnoses, t.emptyStateDescription, t.emptyStateTitle]);

  const [activeIndex, setActiveIndex] = useState(0);
  const [touchStartX, setTouchStartX] = useState<number | null>(null);

  const goTo = (index: number) => {
    const clamped = Math.max(0, Math.min(cards.length - 1, index));
    setActiveIndex(clamped);
  };

  const onTouchStart = (event: React.TouchEvent<HTMLDivElement>) => {
    setTouchStartX(event.touches[0]?.clientX ?? null);
  };

  const onTouchEnd = (event: React.TouchEvent<HTMLDivElement>) => {
    if (touchStartX === null) {
      return;
    }
    const endX = event.changedTouches[0]?.clientX ?? touchStartX;
    const deltaX = endX - touchStartX;
    const minSwipe = 36;

    if (deltaX <= -minSwipe) {
      goTo(activeIndex + 1);
    } else if (deltaX >= minSwipe) {
      goTo(activeIndex - 1);
    }
    setTouchStartX(null);
  };

  return (
    <ScreenContainer className="bg-[#FAFAFA] dark:bg-black transition-colors duration-300">
      <div className="pt-20 px-6 pb-6 border-b border-gray-100 flex justify-between items-end dark:border-white/10 bg-white dark:bg-black transition-colors duration-300">
        <div>
          <h2 className="text-3xl font-sans font-medium text-onyx dark:text-white transition-colors duration-300">
            {t.title}
          </h2>
          <div className="flex items-center gap-2 mt-2">
            <span className="text-[10px] font-bold text-onyx uppercase tracking-widest dark:text-white">
              GAP
            </span>
            <span className="w-8 h-px bg-gray-300 dark:bg-gray-600"></span>
            <span className="text-[10px] font-mono text-gray-400 uppercase dark:text-[#A3A3A3]">
              {String(cards.length).padStart(2, '0')}
            </span>
          </div>
        </div>
        <AlertTriangle size={20} className="text-onyx dark:text-white" />
      </div>

      <div className="flex-1 px-6 py-8 flex flex-col gap-6 bg-[#FAFAFA] dark:bg-black transition-colors duration-300">
        <div
          className="relative overflow-hidden rounded-2xl shadow-xl shadow-gray-200/50 dark:shadow-none"
          onTouchStart={onTouchStart}
          onTouchEnd={onTouchEnd}
        >
          <div
            className="flex transition-transform duration-300 ease-out"
            style={{ transform: `translateX(-${activeIndex * 100}%)` }}
          >
            {cards.map((card) => (
              <article
                key={card.id}
                className="w-full shrink-0 bg-white border border-gray-200 p-8 min-h-[320px] dark:bg-[#3B3B3D] dark:border-white/5 transition-colors duration-300"
              >
                <div className="inline-flex items-center rounded-full border border-gray-200 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.15em] text-onyx dark:text-white dark:border-white/15">
                  {{
                    'investment related': t.investmentLabel,
                    'insurance related': t.insuranceLabel,
                    'spending related': t.spendingLabel,
                    'liability related': t.liabilityLabel,
                  }[card.category]}
                </div>
                <h3 className="mt-6 text-2xl font-sans font-medium text-onyx leading-tight dark:text-white transition-colors duration-300">
                  {card.title}
                </h3>
                <p className="mt-4 text-sm leading-relaxed text-gray-500 font-sans whitespace-pre-wrap dark:text-[#E6E6E7] transition-colors duration-300">
                  {card.description}
                </p>
              </article>
            ))}
          </div>
        </div>

        <div className="flex items-center justify-center gap-3">
          {cards.map((card, index) => (
            <button
              key={card.id}
              type="button"
              aria-label={`Go to diagnosis card ${index + 1}`}
              onClick={() => goTo(index)}
              className={`h-2.5 w-2.5 rounded-full transition-all duration-300 ${index === activeIndex
                ? 'bg-onyx dark:bg-white'
                : 'border border-gray-300 dark:border-gray-700'
                }`}
            />
          ))}
        </div>

        <div className="mt-auto pb-4">
          <PrimaryButton
            className="h-14 shadow-lg"
            onClick={onNext}
            showArrow={true}
          >
            {t.button}
          </PrimaryButton>
        </div>
      </div>
    </ScreenContainer>
  );
};
