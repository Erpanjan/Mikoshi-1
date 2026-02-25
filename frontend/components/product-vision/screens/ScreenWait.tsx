import React from 'react';
import { useScreenTranslation } from '../hooks/useScreenTranslation';
import { ScreenContainer } from '../shared/ScreenContainer';
import { PrimaryButton } from '../shared/PrimaryButton';

export const ScreenWait = ({
    isLoading,
    error,
    onRetry,
}: {
    isLoading: boolean;
    error: string | null;
    onRetry: () => void;
}) => {
    const t = useScreenTranslation('screenWait');

    return (
        <ScreenContainer className="justify-center items-center px-8">
            <div className="flex flex-col items-center justify-center space-y-8 animate-in fade-in duration-700">
                {isLoading ? (
                    <div className="relative w-20 h-20">
                        <div className="absolute inset-0 border-4 border-gray-100 rounded-full dark:border-white/5"></div>
                        <div className="absolute inset-0 border-4 border-onyx border-t-transparent rounded-full animate-spin dark:border-white dark:border-t-transparent transition-colors duration-300"></div>
                    </div>
                ) : (
                    <div className="w-20 h-20 rounded-full border-4 border-red-200 flex items-center justify-center dark:border-red-900/40">
                        <span className="text-red-600 dark:text-red-400 text-2xl">!</span>
                    </div>
                )}

                <div className="text-center space-y-3">
                    <h2 className="text-2xl font-sans font-medium text-onyx dark:text-white transition-colors duration-300">
                        {isLoading ? t.title : 'Policy generation failed'}
                    </h2>
                    <p className="text-gray-400 font-sans text-sm tracking-wide dark:text-[#A3A3A3]">
                        {isLoading ? t.subtitle : (error || 'Please retry the policy pipeline.')}
                    </p>
                </div>
                {!isLoading ? (
                    <div className="w-full px-6">
                        <PrimaryButton onClick={onRetry}>Retry</PrimaryButton>
                    </div>
                ) : null}
            </div>
        </ScreenContainer>
    );
};
