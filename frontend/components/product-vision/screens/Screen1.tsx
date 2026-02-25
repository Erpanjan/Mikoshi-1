import React from 'react';
import { ArrowRight } from 'lucide-react';
import { useScreenTranslation } from '../hooks/useScreenTranslation';
import { ScreenContainer } from '../shared/ScreenContainer';

interface Screen1Props {
  onNext?: () => void;
}

export const Screen1 = ({ onNext }: Screen1Props) => {
  const t = useScreenTranslation('screen1');

  return (
    <ScreenContainer className="p-8 pt-32 relative animate-in fade-in duration-1000">
      <div className="space-y-12 z-10">
        <h1 className="text-5xl font-sans font-medium leading-[0.95] tracking-tight text-onyx dark:text-white transition-colors duration-300">
          {t.title}
        </h1>
        <p className="text-gray-500 text-sm leading-relaxed max-w-[240px] pl-4 border-l border-gray-200 font-sans dark:text-[#E6E6E7] dark:border-[#3B3B3D] transition-colors duration-300">
          {t.description}
        </p>
      </div>
      <div className="mt-auto pb-12 z-10">
        <div
          onClick={onNext}
          className="flex items-center justify-between bg-gray-50 rounded-xl p-6 cursor-pointer group hover:bg-gray-100 transition-colors dark:bg-[#3B3B3D] dark:hover:bg-white dark:group-hover:text-onyx"
        >
          <span className="text-xs font-bold uppercase tracking-[0.2em] text-onyx dark:text-white dark:group-hover:text-onyx transition-colors duration-300">
            {t.button}
          </span>
          <ArrowRight
            size={16}
            className="text-onyx group-hover:translate-x-2 transition-transform dark:text-white dark:group-hover:text-onyx"
          />
        </div>
      </div>
    </ScreenContainer>
  );
};
