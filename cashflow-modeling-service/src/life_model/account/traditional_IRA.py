# Copyright 2025 Spencer Williams
#
# Use of this source code is governed by an MIT license:
# https://github.com/sw23/life-model/blob/main/LICENSE
from typing import Dict, Optional, TYPE_CHECKING
from ..people.person import Person
from ..base_classes import Investment
from ..model import compound_interest

if TYPE_CHECKING:
    from ..montecarlo.market_assumptions import MarketAssumptions


class TraditionalIRA(Investment):
    def __init__(self, person: Person, balance: float = 0, growth_rate: float = 7.0,
                 contribution_limit: float = 6500,
                 asset_allocation: Optional[Dict[str, float]] = None,
                 market_assumptions: Optional['MarketAssumptions'] = None):
        """ Models a Traditional IRA account for a person

        Args:
            person: The person to which this IRA belongs
            balance: Current balance in the IRA
            growth_rate: Expected annual growth rate percentage (fallback if no allocation)
            contribution_limit: Annual contribution limit
            asset_allocation: Optional dict mapping asset class names to weights.
                            When provided, expected return is derived from allocation.
            market_assumptions: Optional MarketAssumptions for deriving return/volatility.
        """
        super().__init__(person, balance, growth_rate)
        self.contribution_limit = contribution_limit
        self.contributions_this_year = 0
        self._asset_allocation = asset_allocation
        self._market_assumptions = market_assumptions
        self._account_id = f"traditional_ira_{id(self)}"
        self._stochastic_growth_applied = False
        
        # Cached derived values
        self._derived_expected_return: Optional[float] = None
        self._derived_volatility: Optional[float] = None
        
        if asset_allocation is not None:
            self._calculate_derived_params()

    def _calculate_derived_params(self):
        """Calculate expected return and volatility from asset allocation."""
        if self._asset_allocation is None:
            self._derived_expected_return = None
            self._derived_volatility = None
            return
        
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
        """Set the asset allocation for this account."""
        if value is not None:
            total = sum(value.values())
            if abs(total - 1.0) > 0.001:
                raise ValueError(f"Asset allocation must sum to 1.0, got {total}")
        self._asset_allocation = value
        self._calculate_derived_params()
    
    @property
    def account_id(self) -> str:
        """Unique identifier for this account."""
        return self._account_id
    
    @property
    def effective_growth_rate(self) -> float:
        """Get effective growth rate (derived from allocation or fixed)."""
        if self._derived_expected_return is not None:
            return self._derived_expected_return * 100
        return self.growth_rate

    def apply_stochastic_return(self, return_rate: float) -> float:
        """Apply a stochastic return rate (used in Monte Carlo mode)."""
        growth = self.balance * return_rate
        self.balance += growth
        self.stat_growth_history.append(growth)
        self._stochastic_growth_applied = True
        return growth

    def apply_growth(self):
        """Apply calculated growth to balance."""
        if self._stochastic_growth_applied:
            self._stochastic_growth_applied = False
            return 0
        growth = self.calculate_growth()
        self.balance += growth
        self.stat_growth_history.append(growth)
        return growth

    def contribute(self, amount: float) -> float:
        """Make a contribution to the IRA

        Args:
            amount: Amount to contribute

        Returns:
            Amount actually contributed (limited by contribution limit)
        """
        available_limit = self.contribution_limit - self.contributions_this_year
        actual_contribution = min(amount, available_limit)

        if actual_contribution > 0:
            self.balance += actual_contribution
            self.contributions_this_year += actual_contribution

        return actual_contribution

    def get_balance(self) -> float:
        """Get current account balance"""
        return self.balance

    def deposit(self, amount: float) -> bool:
        """Deposit amount into account. Returns success status"""
        if amount <= 0:
            return False
        contribution = self.contribute(amount)
        return contribution > 0

    def withdraw(self, amount: float) -> float:
        """Withdraw amount from account. Returns actual amount withdrawn"""
        if amount <= 0:
            return 0.0
        # Traditional IRA withdrawals may have penalties, but for simplicity
        # we'll just allow withdrawals up to the balance
        amount_withdrawn = min(self.balance, amount)
        self.balance -= amount_withdrawn
        return amount_withdrawn

    def calculate_growth(self) -> float:
        """Calculate investment growth for the period using effective growth rate."""
        return compound_interest(self.balance, self.effective_growth_rate, 1, 1)

    def reset_annual_contributions(self):
        """Reset annual contribution tracking (called at year end)"""
        self.contributions_this_year = 0

    def _repr_html_(self):
        desc = '<ul>'
        desc += f'<li>Balance: ${self.balance:,.2f}</li>'
        desc += f'<li>Growth Rate: {self.growth_rate}%</li>'
        desc += f'<li>Contribution Limit: ${self.contribution_limit:,.2f}</li>'
        desc += f'<li>Contributions This Year: ${self.contributions_this_year:,.2f}</li>'
        desc += '</ul>'
        return desc
