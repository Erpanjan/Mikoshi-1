export interface PolicyMenu {
  title: string;
  summary: string;
}

export interface PolicySection {
  id: string;
  title: string;
  content: string;
}

export interface PolicySecurity {
  id: string;
  name: string;
  allocation_pct: number;
  allocation_amount: number;
  management_style?: string;
  asset_class?: string | null;
}

export interface PolicyPortfolio {
  currency?: string;
  total_value?: number | null;
  securities: PolicySecurity[];
}

export interface PolicyDetail {
  title: string;
  sections: PolicySection[];
  portfolio: PolicyPortfolio;
}

export interface PolicyExecution {
  remedy_name?: string;
  funding_source?: string;
  total_transfer?: number;
  currency?: string;
}

export interface FinalPolicy {
  proposal_count: number;
  proposal_index: number;
  menu: PolicyMenu;
  detail: PolicyDetail;
  execution?: PolicyExecution;
}

export interface ConsultationTurn {
  role: 'user' | 'agent';
  message: string;
  timestamp: number;
}
