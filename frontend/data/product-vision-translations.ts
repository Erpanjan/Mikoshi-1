const en = {
  screen1: {
    title: 'Build Your Financial Future',
    description: 'A guided journey from discovery to policy execution in a single mobile workflow.',
    button: 'Continue',
  },
  screen2: {
    title: 'Account Opening',
    subtitle: 'Verification Flow',
    steps: {
      biometric: { text: 'Biometric identity', sub: 'Identity verification' },
      address: { text: 'Address check', sub: 'KYC compliance' },
      banking: { text: 'Banking connection', sub: 'Optional data sync' },
      insurance: { text: 'Insurance connection', sub: 'Optional policy sync' },
    },
    verified: 'Verified',
    linked: 'Linked',
    button: {
      begin: 'Begin Consultation',
      verifying: 'Verifying...',
    },
  },
  screen3: {
    question: 'What does financial confidence look like for you in 10 years?',
    status: {
      resume: 'Resume',
      speaking: 'Speaking',
      listening: 'Listening',
    },
  },
  screenWait: {
    title: 'Policy is being developed',
    subtitle: 'Please wait...',
  },
  screen4: {
    header: 'Solution',
    proposal: 'Proposal 01',
    title: 'Policy Option',
    description: 'A defensive allocation model designed to preserve optionality while maintaining growth potential.',
    button: 'View Details',
  },
  screen5: {
    header: 'Policy Breakdown',
    sections: {
      strategy: 'Strategy',
      allocation: 'Allocation',
      instruments: 'Instruments',
      impact: 'Impact',
    },
    strategy: {
      trapTitle: 'Typical Risk Trap',
      trapDesc: 'Unplanned liquidity shocks can force untimely liquidation of long-term positions.',
      forcedLiquidation: 'Forced liquidation zone',
      solutionTitle: 'Recommended Mitigation',
      solutionDesc: 'Keep a dedicated liquidity reserve and diversify volatility-sensitive assets.',
    },
    allocation: {
      equity: 'Equity',
      alts: 'Alternatives',
      fixedInc: 'Fixed Income',
      cash: 'Cash',
    },
    instruments: {
      fixedIncome: 'Fixed Income Sleeve',
      equity: 'Equity Sleeve',
      alternatives: 'Alternatives Sleeve',
    },
    impact: {
      expReturn: 'Expected Return',
      volatility: 'Volatility',
      scenario: 'Stress Scenario',
      scenarioLabel: 'Recession',
      market: 'Market',
      portfolio: 'Portfolio',
      quote: 'This structure balances growth with downside resilience under stressed conditions.',
    },
  },
  screenFinancialDiagnoses: {
    title: 'Financial Diagnoses',
    subtitle: 'Swipe to review each identified gap before policy details.',
    investmentLabel: 'Investment Related',
    insuranceLabel: 'Insurance Related',
    spendingLabel: 'Spending Related',
    liabilityLabel: 'Liability Related',
    emptyStateTitle: 'No diagnoses available',
    emptyStateDescription: 'No financial diagnosis gaps were returned from the client profile analysis.',
    button: 'Policy Selection',
  },
  screen6: {
    title: 'Execute Policy',
    selectedRemedy: 'Selected policy',
    remedyName: 'Solution',
    fundingSource: 'Funding source',
    accountName: 'Primary Portfolio Account',
    verified: 'Verified',
    totalTransfer: 'Total transfer',
    amount: 'HK$ 2,500,000',
    button: 'Authorize Allocation',
    secure: 'Bank-grade secure authorization',
  },
  screen7: {
    title: 'Active Monitoring',
    chat: {
      system1: 'Today 09:24',
      system2: 'Today 09:26',
      agent1: 'I have identified market drift in your alternatives sleeve. I prepared a short briefing for you.',
      agent2: 'Would you like a quick walkthrough of the risk implications?',
      agent3: 'I can explain now, generate a report, or schedule a review call.',
      pitch: 'Watch AI Briefing',
      buttons: {
        explain: 'Explain',
        report: 'Report',
        review: 'Schedule Review',
      },
    },
    reply: 'Reply to agent',
  },
};

export const productVisionTranslations = {
  en,
} as const;
