import React, { ReactNode, HTMLAttributes } from 'react';

interface ScreenContainerProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  className?: string;
}

export const ScreenContainer = ({ children, className = '', ...props }: ScreenContainerProps) => {
  return (
    <div
      className={`h-full flex flex-col bg-white dark:bg-black transition-all duration-300 ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};
