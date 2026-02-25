import React from 'react';
import { Lock, Check } from 'lucide-react';
import { useScreenTranslation } from '../hooks/useScreenTranslation';
import { useStepProgress, Step } from '../hooks/useStepProgress';
import { ScreenContainer } from '../shared/ScreenContainer';
import { PrimaryButton } from '../shared/PrimaryButton';

export const Screen2 = ({ onNext }: { onNext?: () => void }) => {
  const t = useScreenTranslation('screen2');

  const initialSteps: Step[] = [
    { id: 1, key: 'biometric', status: "pending", type: "verified" },
    { id: 2, key: 'address', status: "pending", type: "verified" },
    { id: 3, key: 'banking', status: "pending", type: "optional" },
    { id: 4, key: 'insurance', status: "pending", type: "optional" },
  ];

  const { steps, completeStep } = useStepProgress(initialSteps);
  const isComplete = steps.every(s => s.status === "done");

  return (
    <ScreenContainer>
      <div className="pt-24 pb-8 px-6 border-b border-gray-100 dark:border-white/10">
        <div className="flex justify-between items-end">
          <h2 className="text-3xl font-sans font-medium tracking-tight text-onyx dark:text-white transition-colors duration-300">
            {t.title}
          </h2>
          <Lock size={16} className="text-onyx mb-1 dark:text-white" />
        </div>
        <p className="text-[10px] font-bold text-gray-400 mt-2 uppercase tracking-[0.2em] dark:text-[#A3A3A3]">
          {t.subtitle}
        </p>
      </div>
      <div className="flex-1 pt-0">
        {steps.map((item) => {
          const stepT = t.steps[item.key as keyof typeof t.steps];
          return (
            <div
              key={item.id}
              onClick={() => completeStep(item.id)}
              className="flex items-stretch border-b border-gray-100 transition-all duration-500 group hover:bg-gray-50 dark:border-white/10 dark:hover:bg-[#3B3B3D] cursor-pointer"
            >
              <div className="w-16 flex items-center justify-center">
                <div
                  className={`w-5 h-5 border flex items-center justify-center transition-all duration-500 rounded-lg ${item.status === "done"
                    ? "border-onyx bg-onyx dark:border-white dark:bg-white"
                    : "border-gray-200 dark:border-[#3B3B3D]"
                    }`}
                >
                  {item.status === "done" && (
                    <Check size={12} className="text-white dark:text-onyx" />
                  )}
                </div>
              </div>
              <div className="p-6 pl-0 flex-1 flex justify-between items-center">
                <div>
                  <p
                    className={`text-sm font-medium transition-colors duration-500 uppercase tracking-wide ${item.status === "done"
                      ? "text-onyx dark:text-white"
                      : "text-gray-400 dark:text-[#A3A3A3]"
                      }`}
                  >
                    {stepT.text}
                  </p>
                  <p className="text-[9px] font-mono text-gray-400 mt-1 tracking-wider dark:text-[#A3A3A3]">
                    {stepT.sub}
                  </p>
                </div>
                {item.status === "done" && (
                  <span
                    className={`text-[9px] font-bold px-2 py-1 border ${item.type === "verified"
                      ? "border-onyx text-onyx dark:border-white dark:text-white"
                      : "border-gray-200 text-gray-400 dark:border-[#3B3B3D] dark:text-[#A3A3A3]"
                      }`}
                  >
                    {item.type === "verified" ? t.verified : t.linked}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
      <div className="p-6">
        <PrimaryButton
          onClick={isComplete ? onNext : undefined}
          disabled={!isComplete}
          variant={isComplete ? 'default' : 'loading'}
          showArrow={true}
        >
          {isComplete ? t.button.begin : t.button.verifying}
        </PrimaryButton>
      </div>
    </ScreenContainer>
  );
};
