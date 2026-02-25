import { useState } from 'react';

export interface Step {
  id: number;
  key: string;
  status: 'pending' | 'done';
  type?: 'verified' | 'optional';
}

export const useStepProgress = (initialSteps: Step[]) => {
  const [steps, setSteps] = useState<Step[]>(initialSteps);

  const completeStep = (id: number) => {
    setSteps((prev) =>
      prev.map((s) =>
        s.id === id ? { ...s, status: "done" } : s
      )
    );
  };

  return { steps, completeStep };
};


