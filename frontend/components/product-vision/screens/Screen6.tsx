import React from 'react';
import { Lock, Shield, Fingerprint } from 'lucide-react';
import { useScreenTranslation } from '../hooks/useScreenTranslation';
import { ScreenContainer } from '../shared/ScreenContainer';
import { PrimaryButton } from '../shared/PrimaryButton';
import type { PolicyExecution } from '@/lib/policy/types';

interface Screen6Props {
  onExecute: () => void;
  execution?: PolicyExecution;
  fallbackCurrency?: string;
}

const BANK_NAME_OPTIONS = [
  'HSBC Premier',
  'Citi Private Bank',
  'JPMorgan Private Bank',
  'Standard Chartered Priority',
  'Bank of America Private Bank',
];

const hashToNumber = (value: string): number => {
  let hash = 0;
  for (let i = 0; i < value.length; i += 1) {
    hash = (hash * 31 + value.charCodeAt(i)) >>> 0;
  }
  return hash;
};

const inferBankName = (fundingSource?: string): string => {
  const source = String(fundingSource || '').trim();
  if (!source) {
    return BANK_NAME_OPTIONS[0];
  }
  const firstChunk = source.split('—')[0]?.split('-')[0]?.trim() || '';
  if (firstChunk.length >= 3) {
    return firstChunk;
  }
  return BANK_NAME_OPTIONS[hashToNumber(source) % BANK_NAME_OPTIONS.length];
};

const inferMaskedAccount = (seedInput: string): string => {
  const hash = hashToNumber(seedInput || 'default-seed');
  const last4 = String((hash % 9000) + 1000);
  return `•••• ${last4}`;
};

const formatTransfer = (currencyCode: string, amount?: number): string => {
  if (typeof amount !== 'number' || !Number.isFinite(amount)) {
    return 'TBD';
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currencyCode || 'USD',
    maximumFractionDigits: 0,
  }).format(amount);
};

export const Screen6 = ({ onExecute, execution, fallbackCurrency = 'USD' }: Screen6Props) => {
  const t = useScreenTranslation('screen6');
  const remedyName = execution?.remedy_name || t.remedyName;
  const bankName = inferBankName(execution?.funding_source);
  const maskedAccount = inferMaskedAccount(`${execution?.funding_source || ''}|${execution?.remedy_name || ''}`);
  const transferCurrency = execution?.currency || fallbackCurrency || 'USD';
  const transferAmount = formatTransfer(transferCurrency, execution?.total_transfer);

  // The "old version" uses a darker theme and specific red accent color for the button (#FF3333)
  // We keep this structure but adapt it for light/dark mode support.
  // Dark mode keeps the original look. Light mode uses white background and appropriate text colors.

  return (
    <ScreenContainer className="dark:bg-[#0F0F0F]">
      <div className="absolute inset-0 bg-[#111] opacity-[0.05] dark:opacity-50 z-0 pointer-events-none transition-opacity duration-300">
        <div
          className="w-full h-full opacity-10"
          style={{
            backgroundImage: "radial-gradient(currentColor 1px, transparent 1px)",
            backgroundSize: "20px 20px",
          }}
        ></div>
      </div>
      <div className="mt-auto border-t rounded-t-3xl z-10 p-8 pb-12 shadow-[0_-10px_40px_rgba(0,0,0,0.5)] transition-colors duration-300 dark:bg-[#1A1A1A] dark:border-[#333] bg-white border-gray-200 shadow-[0_-10px_40px_rgba(0,0,0,0.1)]">
        <div className="w-12 h-1 mx-auto rounded-full mb-8 transition-colors duration-300 dark:bg-[#333] bg-gray-200"></div>
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-xl font-medium transition-colors duration-300 dark:text-white text-onyx">
            {t.title}
          </h2>
          <Lock size={16} className="transition-colors duration-300 dark:text-white text-onyx" />
        </div>
        <div className="space-y-4 mb-8">
          <div className="flex justify-between py-4 border-b transition-colors duration-300 dark:border-[#333] border-gray-100">
            <span className="text-sm transition-colors duration-300 dark:text-gray-500 text-gray-400">{t.selectedRemedy}</span>
            <span className="text-sm transition-colors duration-300 dark:text-white text-onyx">
              {remedyName}
            </span>
          </div>
          <div className="flex justify-between py-4 border-b transition-colors duration-300 dark:border-[#333] border-gray-100">
            <span className="text-sm transition-colors duration-300 dark:text-gray-500 text-gray-400">{t.fundingSource}</span>
            <div className="text-right">
              <span className="text-sm block transition-colors duration-300 dark:text-white text-onyx">
                {bankName}
              </span>
              <span className="text-[10px] font-mono block transition-colors duration-300 dark:text-gray-300 text-gray-600">
                {maskedAccount}
              </span>
              <span className="text-[10px] font-mono transition-colors duration-300 dark:text-[#00FF00] text-green-600">
                {t.verified}
              </span>
            </div>
          </div>
          <div className="flex justify-between py-4 border-b transition-colors duration-300 dark:border-[#333] border-gray-100">
            <span className="text-sm transition-colors duration-300 dark:text-gray-500 text-gray-400">{t.totalTransfer}</span>
            <span className="text-xl font-mono transition-colors duration-300 dark:text-white text-onyx">
              {transferAmount}
            </span>
          </div>
        </div>
        <PrimaryButton
          onClick={onExecute}
          variant="danger"
          icon={<Fingerprint size={24} />}
        >
          {t.button}
        </PrimaryButton>
        <p className="text-center text-[9px] mt-6 flex items-center justify-center gap-2 transition-colors duration-300 dark:text-gray-600 text-gray-400">
          <Shield size={10} /> {t.secure}
        </p>
      </div>
    </ScreenContainer>
  );
};
