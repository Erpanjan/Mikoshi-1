# Copyright 2025 Spencer Williams
#
# Use of this source code is governed by an MIT license:
# https://github.com/sw23/life-model/blob/main/LICENSE
import html
from typing import Dict, Optional, TYPE_CHECKING
from ..people.person import Person
from ..base_classes import Investment

if TYPE_CHECKING:
    from ..montecarlo.market_assumptions import MarketAssumptions


class BrokerageAccount(Investment):
    def __init__(self, person: Person, company: str,
                 balance: float = 0, growth_rate: float = 7.0,
                 asset_allocation: Optional[Dict[str, float]] = None,
                 market_assumptions: Optional['MarketAssumptions'] = None):
        """ Models a brokerage/investment account

        Args:
            person: The person who owns this account
            company: Brokerage company name
            balance: Current account balance
            growth_rate: Expected annual growth rate percentage (fallback if no allocation)
            asset_allocation: Optional dict mapping asset class names to weights
                            (e.g., {"us_large_cap": 0.6, "us_bonds": 0.4}).
                            When provided with market_assumptions, the expected return
                            and volatility are derived from the allocation.
                            Weights should sum to 1.0.
            market_assumptions: Optional MarketAssumptions for deriving return/volatility
                              from asset_allocation. If None but allocation is provided,
                              will use default assumptions.
        """
        super().__init__(person, balance, growth_rate)
        self.company = company
        self.investments = []  # List of individual investments
        self._asset_allocation = asset_allocation
        self._market_assumptions = market_assumptions
        self._account_id = f"brokerage_{id(self)}"
        self._stochastic_growth_applied = False  # Track if MC growth was applied this step
        
        # Cached derived values from asset allocation
        self._derived_expected_return: Optional[float] = None
        self._derived_volatility: Optional[float] = None
        
        # Calculate derived values if allocation is provided
        if asset_allocation is not None:
            self._calculate_derived_params()

    def _calculate_derived_params(self):
        """Calculate expected return and volatility from asset allocation."""
        if self._asset_allocation is None:
            self._derived_expected_return = None
            self._derived_volatility = None
            return
        
        # Get or create market assumptions
        market = self._market_assumptions
        if market is None:
            from ..montecarlo.market_assumptions import MarketAssumptions
            market = MarketAssumptions.create_default()
            self._market_assumptions = market
        
        from ..montecarlo.account_parameters import AccountParametersCalculator
        calc = AccountParametersCalculator(market)
        params = calc.calculate_account_params(self._account_id, self._asset_allocation)
        
        self._derived_expected_return = params.expected_return
        self._derived_volatility = params.volatility

    @property
    def asset_allocation(self) -> Optional[Dict[str, float]]:
        """Get the asset allocation for this account."""
        return self._asset_allocation
    
    @asset_allocation.setter
    def asset_allocation(self, value: Optional[Dict[str, float]]):
        """Set the asset allocation for this account.
        
        Args:
            value: Dict mapping asset class names to weights, or None
        
        Raises:
            ValueError: If weights don't sum to approximately 1.0
        """
        if value is not None:
            total = sum(value.values())
            if abs(total - 1.0) > 0.001:
                raise ValueError(f"Asset allocation must sum to 1.0, got {total}")
        self._asset_allocation = value
        self._calculate_derived_params()
    
    @property
    def market_assumptions(self) -> Optional['MarketAssumptions']:
        """Get the market assumptions used for this account."""
        return self._market_assumptions
    
    @market_assumptions.setter
    def market_assumptions(self, value: Optional['MarketAssumptions']):
        """Set market assumptions and recalculate derived params."""
        self._market_assumptions = value
        if self._asset_allocation is not None:
            self._calculate_derived_params()
    
    @property
    def derived_expected_return(self) -> Optional[float]:
        """Get expected return derived from asset allocation (as decimal, e.g., 0.08 for 8%)."""
        return self._derived_expected_return
    
    @property
    def derived_volatility(self) -> Optional[float]:
        """Get volatility derived from asset allocation (as decimal, e.g., 0.15 for 15%)."""
        return self._derived_volatility
    
    @property
    def effective_growth_rate(self) -> float:
        """Get the effective growth rate used for deterministic calculations.
        
        If asset allocation is provided, uses derived expected return.
        Otherwise, falls back to the fixed growth_rate parameter.
        
        Returns:
            Growth rate as percentage (e.g., 7.0 for 7%)
        """
        if self._derived_expected_return is not None:
            return self._derived_expected_return * 100  # Convert to percentage
        return self.growth_rate
    
    @property
    def account_id(self) -> str:
        """Unique identifier for this account (used in Monte Carlo simulation)."""
        return self._account_id

    def apply_stochastic_return(self, return_rate: float) -> float:
        """Apply a stochastic return rate (used in Monte Carlo mode).
        
        This method is called by the InvestmentAccountRegistry during
        probabilistic simulation to apply correlated returns.
        
        Args:
            return_rate: Annual return as decimal (e.g., 0.08 for 8%)
        
        Returns:
            The growth amount applied
        """
        growth = self.balance * return_rate
        self.balance += growth
        self.stat_growth_history.append(growth)
        self._stochastic_growth_applied = True
        return growth

    def calculate_growth(self) -> float:
        """Calculate investment growth based on effective growth rate.
        
        Uses derived expected return from asset allocation if available,
        otherwise falls back to the fixed growth_rate parameter.
        """
        return self.balance * (self.effective_growth_rate / 100)

    def apply_growth(self):
        """Apply calculated growth to balance.
        
        In Monte Carlo mode, if stochastic return was already applied,
        skip deterministic growth to avoid double-counting.
        """
        if self._stochastic_growth_applied:
            # Reset flag for next step; stochastic growth already applied
            self._stochastic_growth_applied = False
            return 0
        
        # Deterministic mode: apply normal growth
        growth = self.calculate_growth()
        self.balance += growth
        self.stat_growth_history.append(growth)
        return growth

    def get_balance(self) -> float:
        return self.balance

    def deposit(self, amount: float) -> bool:
        if amount < 0:
            raise ValueError("Deposit amount cannot be negative")
        self.balance += amount
        return True

    def withdraw(self, amount: float) -> float:
        if amount < 0:
            return 0.0  # Cannot withdraw negative amounts
        actual_withdrawal = min(amount, self.balance)
        self.balance -= actual_withdrawal
        return actual_withdrawal

    def _repr_html_(self):
        desc = '<ul>'
        desc += f'<li>Company: {html.escape(self.company)}</li>'
        desc += f'<li>Balance: ${self.balance:,.2f}</li>'
        if self._asset_allocation:
            desc += '<li>Asset Allocation: '
            alloc_str = ', '.join(f'{k}: {v:.0%}' for k, v in self._asset_allocation.items())
            desc += html.escape(alloc_str)
            desc += '</li>'
            if self._derived_expected_return is not None:
                desc += f'<li>Expected Return: {self._derived_expected_return:.2%} (derived from allocation)</li>'
            if self._derived_volatility is not None:
                desc += f'<li>Volatility: {self._derived_volatility:.2%}</li>'
        else:
            desc += f'<li>Growth Rate: {self.growth_rate}% (fixed)</li>'
        desc += '</ul>'
        return desc
