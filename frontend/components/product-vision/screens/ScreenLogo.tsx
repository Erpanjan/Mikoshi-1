import React, { useState } from 'react';
import { ScreenContainer } from '../shared/ScreenContainer';

interface ScreenLogoProps {
  onNext?: () => void;
}

export const ScreenLogo = ({ onNext }: ScreenLogoProps) => {
  const [isFadingOut, setIsFadingOut] = useState(false);

  const handleClick = () => {
    if (isFadingOut) return;
    setIsFadingOut(true);
    // Wait for fade out animation before proceeding
    setTimeout(() => {
      onNext?.();
    }, 600);
  };

  return (
    <ScreenContainer
      className={`items-center justify-center relative cursor-pointer transition-opacity duration-700 ${isFadingOut ? 'opacity-0' : 'opacity-100'}`}
      onClick={handleClick}
    >
      <div className={`animate-in fade-in zoom-in duration-1000 text-center`}>
        <h1 className="text-6xl font-sans font-bold tracking-tighter text-onyx dark:text-white transition-colors duration-300">
          ARK
        </h1>
      </div>
    </ScreenContainer>
  );
};
