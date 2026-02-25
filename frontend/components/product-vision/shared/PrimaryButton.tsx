import React, { ReactNode } from 'react';
import { ArrowRight } from 'lucide-react';

interface PrimaryButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  icon?: ReactNode;
  showArrow?: boolean;
  fullWidth?: boolean;
  variant?: 'default' | 'danger' | 'loading';
}

export const PrimaryButton = ({ 
  children, 
  icon, 
  showArrow = false, 
  fullWidth = true, 
  variant = 'default',
  className = '',
  ...props 
}: PrimaryButtonProps) => {
  const baseClasses = "text-xs font-bold uppercase tracking-[0.2em] transition-all duration-300 flex items-center justify-center gap-4 rounded-xl";
  
  const variants = {
    default: "bg-onyx text-white hover:bg-black dark:bg-white dark:text-onyx dark:hover:bg-white",
    danger: "bg-[#FF3333] hover:bg-[#CC0000] text-white",
    loading: "bg-white text-gray-300 cursor-wait border-t border-gray-100 dark:bg-[#3B3B3D] dark:text-[#A3A3A3] dark:border-white/10"
  };

  const widthClass = fullWidth ? "w-full" : "";
  const heightClass = "h-16"; // Standard height across most screens, override in className if needed

  return (
    <button
      className={`${baseClasses} ${variants[variant]} ${widthClass} ${heightClass} ${className}`}
      {...props}
    >
      {icon}
      <span>{children}</span>
      {showArrow && <ArrowRight size={16} className={variant === 'default' ? "group-hover:translate-x-1 transition-transform" : ""} />}
    </button>
  );
};

