import React from 'react';

export const PhoneFrame = ({
  children,
  statusBarTime = '09:41',
  isDarkMode = false,
}: {
  children: React.ReactNode;
  statusBarTime?: string;
  isDarkMode?: boolean;
}) => {
  return (
    <div
      className={`relative mx-auto bg-white border-[12px] border-white rounded-[3rem] h-[800px] w-[375px] shadow-[0_0_0_1px_rgba(0,0,0,0.05),0_20px_50px_-12px_rgba(0,0,0,0.2)] overflow-hidden ring-1 ring-black/5 dark:bg-[#2A2A2A] dark:border-[#2A2A2A] dark:ring-white/10 transition-colors duration-300 ${isDarkMode ? 'dark' : ''}`}
    >
      {/* Status Bar */}
      <div className="h-[44px] w-full absolute top-0 left-0 right-0 z-50 flex items-end justify-between px-6 pb-2 text-[10px] font-mono tracking-widest uppercase mix-blend-difference text-white">
        <span>{statusBarTime}</span>
        <div className="flex gap-2">
          <span>5G</span>
          <span>100%</span>
        </div>
      </div>

      <style>{`
        .scrollbar-hide::-webkit-scrollbar { display: none; }
        .scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
        @keyframes fade-in {
          from { opacity: 0; transform: translateY(10px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in { animation: fade-in 0.5s ease-out forwards; }
      `}</style>

      <div className="h-full w-full bg-white text-onyx overflow-y-auto scrollbar-hide relative flex flex-col font-sans dark:bg-black dark:text-white transition-colors duration-300">
        {children}
      </div>

      {/* Home indicator */}
      <div className="absolute bottom-2 left-1/2 -translate-x-1/2 w-1/3 h-[5px] bg-black/20 rounded-full z-50 dark:bg-white/20" />
    </div>
  );
};
