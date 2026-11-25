import React from 'react';

interface LogoProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  showWordmark?: boolean;
}

export const CreditPilotLogo: React.FC<LogoProps> = ({
  className = '',
  size = 'md',
  showWordmark = true
}) => {
  const iconSize = size === 'sm' ? 'w-7 h-7' : size === 'lg' ? 'w-10 h-10' : 'w-8 h-8';
  const textSize = size === 'sm' ? 'text-base' : size === 'lg' ? 'text-xl' : 'text-lg';

  return (
    <div className={`flex items-center space-x-3 select-none ${className}`}>
      {/* Custom geometric logo: forward-moving arrow + upward trajectory */}
      <div
        className={`${iconSize} bg-[#191919] rounded-md flex items-center justify-center p-1.5 transition-colors`}
        title="CreditPilot AI"
      >
        <svg
          viewBox="0 0 32 32"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-full h-full text-white"
        >
          {/* Base trajectory line */}
          <path
            d="M5 24L14 15"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
          />
          {/* Upward forward chevron/arrow */}
          <path
            d="M13 9L27 9L27 23"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          {/* Main ascending diagonal flight path */}
          <path
            d="M11 25L26 10"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
          />
        </svg>
      </div>

      {showWordmark && (
        <div className="flex flex-col">
          <div className="flex items-center space-x-1.5">
            <span className={`font-serif tracking-tight text-[#191919] font-medium ${textSize}`}>
              CreditPilot
            </span>
            <span className="text-[11px] font-sans px-1.5 py-0.5 rounded bg-[#F4F3F3] text-[#191919]/70 font-medium border border-[#E5E5E5]">
              AI
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
