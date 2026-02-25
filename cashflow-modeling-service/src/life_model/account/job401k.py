# Copyright 2022 Spencer Williams
#
# Use of this source code is governed by an MIT license:
# https://github.com/sw23/life-model/blob/main/LICENSE

from typing import Optional, Dict, TYPE_CHECKING
from ..model import continous_interest
from ..limits import federal_retirement_age, required_min_distrib
from ..base_classes import RetirementAccount

if TYPE_CHECKING:
    from ..work.job import Job
    from ..montecarlo.market_assumptions import MarketAssumptions


class Job401kAccount(RetirementAccount):
    def __init__(self, job: 'Job',
                 pretax_balance: float = 0, pretax_contrib_percent: float = 0,
                 roth_balance: float = 0, roth_contrib_percent: float = 0,
                 average_growth: float = 0, company_match_percent: float = 0,
                 asset_allocation: Optional[Dict[str, float]] = None,
                 market_assumptions: Optional['MarketAssumptions'] = None):
        """401k Account

        Args:
            job (Job): Job offering the 401k plan.
            pretax_balance (float, optional): Initial pre-tax balance of account. Defaults to 0.
            pretax_contrib_percent (float, optional): Pre-tax contribution percentage. Defaults to 0.
            roth_balance (float, optional): Initial roth balance of account. Defaults to 0.
            roth_contrib_percent (float, optional): Roth contribution percentage. Defaults to 0.
            average_growth (float, optional): Average account growth every year (fallback). Defaults to 0.
            company_match_percent (float, optional): Percentage that company matches contributions. Defaults to 0.
            asset_allocation: Optional dict mapping asset class names to weights.
                            When provided, expected return is derived from allocation.
            market_assumptions: Optional MarketAssumptions for deriving return/volatility.
        """
        super().__init__(job.owner, 0)  # Initialize with 0, we'll handle balance ourselves
        self.job: Optional['Job'] = job
        self.pretax_balance = pretax_balance
        self.pretax_contrib_percent = pretax_contrib_percent
        self.roth_balance = roth_balance
        self.roth_contrib_percent = roth_contrib_percent
        self.average_growth = average_growth
        self.company_match_percent = company_match_percent

        self.stat_required_min_distrib = 0
        self.stat_401k_balance = 0
        
        # Monte Carlo support
        self._asset_allocation = asset_allocation
        self._market_assumptions = market_assumptions
        self._account_id = f"401k_{id(self)}"
        self._stochastic_growth_applied = False
        
        # Cached derived values
        self._derived_expected_return: Optional[float] = None
        self._derived_volatility: Optional[float] = None
        
        if asset_allocation is not None:
            self._calculate_derived_params()

        job.retirement_account = self

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
        """Get effective growth rate (derived from allocation or fixed average_growth)."""
        if self._derived_expected_return is not None:
            return self._derived_expected_return * 100
        return self.average_growth

    def apply_stochastic_return(self, return_rate: float) -> float:
        """Apply a stochastic return rate (used in Monte Carlo mode).
        
        Applies the return proportionally to both pretax and roth balances.
        """
        pretax_growth = self.pretax_balance * return_rate
        roth_growth = self.roth_balance * return_rate
        
        self.pretax_balance += pretax_growth
        self.roth_balance += roth_growth
        
        total_growth = pretax_growth + roth_growth
        self._stochastic_growth_applied = True
        return total_growth

    def pretax_contrib(self, salary: float):
        return salary * (self.pretax_contrib_percent / 100)

    def roth_contrib(self, salary: float):
        return salary * (self.roth_contrib_percent / 100)

    def company_match(self, contribution: float):
        return contribution * (self.company_match_percent / 100)

    @property
    def balance(self):
        return self.pretax_balance + self.roth_balance

    @balance.setter
    def balance(self, value):
        # For Job401k, we don't allow direct balance setting
        # This setter exists to satisfy the parent class requirements
        pass

    def get_balance(self) -> float:
        """Get current account balance"""
        return self.balance

    def deposit(self, amount: float) -> bool:
        """Deposit amount into account. Returns success status"""
        if amount <= 0:
            return False
        # For 401k, deposits go to pretax by default
        self.pretax_balance += amount
        return True

    def withdraw(self, amount: float) -> float:
        """Withdraw amount from account. Returns actual amount withdrawn"""
        if amount <= 0:
            return 0.0
        # Withdraw from pretax first, then roth
        total_withdrawn = 0.0

        if self.pretax_balance > 0:
            pretax_withdrawn = min(self.pretax_balance, amount)
            self.pretax_balance -= pretax_withdrawn
            total_withdrawn += pretax_withdrawn
            amount -= pretax_withdrawn

        if amount > 0 and self.roth_balance > 0:
            roth_withdrawn = min(self.roth_balance, amount)
            self.roth_balance -= roth_withdrawn
            total_withdrawn += roth_withdrawn

        return total_withdrawn

    def _repr_html_(self):
        company = self.job.company if self.job is not None else "<None>"
        return f"401k at {company} balance: ${self.balance:,}"

    # Using pre_step() so taxable_income will be set before person's step() is called
    def pre_step(self):
        # Note: Contributions are handled by job, after this is called.
        # This isn't 100% accurate since contributions aren't included in the
        # growth, which is a little pessimistic but that should be fine.

        # In Monte Carlo mode, skip deterministic growth if stochastic was already applied
        if self._stochastic_growth_applied:
            self._stochastic_growth_applied = False
        else:
            # Deterministic mode: apply continuous interest growth using effective rate
            growth_rate = self.effective_growth_rate
            self.pretax_balance += continous_interest(self.pretax_balance, growth_rate)
            self.roth_balance += continous_interest(self.roth_balance, growth_rate)

        # Balance is automatically calculated by the property

        # Track balance history
        self.stat_balance_history.append(self.balance)
        if (self.person.age > federal_retirement_age()):
            self.stat_useable_balance = self.balance

        # Required minimum distributions
        # - Based on the owner's age, force withdraw the required minium
        required_min_dist_amount = self.deduct_pretax(required_min_distrib(self.person.age, self.pretax_balance))
        self.person.deposit_into_bank_account(required_min_dist_amount)
        self.person.taxable_income += required_min_dist_amount

        self.stat_required_min_distrib = required_min_dist_amount
        self.stat_401k_balance = self.balance

    def deduct_pretax(self, amount: float):
        """Deduct from pre-tax balance

        Args:
            amount (float): Amount to deduct.

        Returns:
            float: Amount deducted. Will not be less than the account balance.
        """
        # TODO - Need to figure out where early penalties and limits are applied
        amount_deducted = min(self.pretax_balance, amount)
        self.pretax_balance -= amount_deducted
        return amount_deducted

    def deduct_roth(self, amount: float) -> float:
        """Deduct from roth balance

        Args:
            amount (float): Amount to deduct.

        Returns:
            float: Amount deducted. Will not be less than the account balance.
        """
        # TODO - Need to figure out where early penalties and limits are applied
        amount_deducted = min(self.roth_balance, amount)
        self.roth_balance -= amount_deducted
        return amount_deducted
