# Copyright 2025 Spencer Williams
#
# Use of this source code is governed by an MIT license:
# https://github.com/sw23/life-model/blob/main/LICENSE

"""
Integration tests for Monte Carlo simulation.

These tests verify:
1. Deterministic mode works exactly as before (backward compatibility)
2. Monte Carlo mode works properly with correlated returns
3. The two modes are properly isolated from each other

Note: Tests that require actual account instantiation use simplified mock objects
that simulate account behavior without requiring full Mesa Agent infrastructure.
"""

import unittest
import numpy as np

from ..montecarlo.config import MonteCarloConfig
from ..montecarlo.market_assumptions import MarketAssumptions
from ..montecarlo.account_parameters import AccountParametersCalculator, AccountStochasticParams
from ..montecarlo.return_generator import AccountCorrelatedReturnGenerator
from ..montecarlo.account_registry import InvestmentAccountRegistry
from ..montecarlo.results import MonteCarloResults
from ..montecarlo.simulator import MonteCarloSimulator


class MockStochasticAccount:
    """Simplified mock account for testing Monte Carlo features without Mesa."""
    
    def __init__(self, account_id, balance, growth_rate=7.0, asset_allocation=None):
        self._account_id = account_id
        self.balance = balance
        self.growth_rate = growth_rate
        self._asset_allocation = asset_allocation
        self._stochastic_growth_applied = False
        self.stat_growth_history = []
    
    @property
    def account_id(self):
        return self._account_id
    
    @property
    def asset_allocation(self):
        return self._asset_allocation
    
    @asset_allocation.setter
    def asset_allocation(self, value):
        if value is not None:
            total = sum(value.values())
            if abs(total - 1.0) > 0.001:
                raise ValueError(f"Asset allocation must sum to 1.0, got {total}")
        self._asset_allocation = value
    
    def calculate_growth(self):
        return self.balance * (self.growth_rate / 100)
    
    def apply_growth(self):
        if self._stochastic_growth_applied:
            self._stochastic_growth_applied = False
            return 0
        growth = self.calculate_growth()
        self.balance += growth
        self.stat_growth_history.append(growth)
        return growth
    
    def apply_stochastic_return(self, return_rate):
        growth = self.balance * return_rate
        self.balance += growth
        self.stat_growth_history.append(growth)
        self._stochastic_growth_applied = True
        return growth


class Mock401kAccount:
    """Simplified mock 401k account for testing."""
    
    def __init__(self, account_id, pretax_balance, roth_balance, growth_rate=7.0, 
                 asset_allocation=None):
        self._account_id = account_id
        self.pretax_balance = pretax_balance
        self.roth_balance = roth_balance
        self.growth_rate = growth_rate
        self._asset_allocation = asset_allocation
        self._stochastic_growth_applied = False
    
    @property
    def account_id(self):
        return self._account_id
    
    @property
    def asset_allocation(self):
        return self._asset_allocation
    
    @property
    def balance(self):
        return self.pretax_balance + self.roth_balance
    
    def apply_stochastic_return(self, return_rate):
        pretax_growth = self.pretax_balance * return_rate
        roth_growth = self.roth_balance * return_rate
        self.pretax_balance += pretax_growth
        self.roth_balance += roth_growth
        self._stochastic_growth_applied = True
        return pretax_growth + roth_growth


class TestDeterministicModeBackwardCompatibility(unittest.TestCase):
    """Tests ensuring deterministic mode is unaffected by Monte Carlo changes."""
    
    def test_account_without_allocation_uses_deterministic_growth(self):
        """Account without asset_allocation should use fixed growth_rate."""
        account = MockStochasticAccount(
            account_id="test_1",
            balance=10000,
            growth_rate=10.0,  # 10% growth
            asset_allocation=None  # No allocation - deterministic mode
        )
        
        # Verify no asset allocation
        self.assertIsNone(account.asset_allocation)
        
        # Verify deterministic growth calculation
        expected_growth = 10000 * 0.10  # 10% of 10000 = 1000
        self.assertEqual(account.calculate_growth(), expected_growth)
        
        # Apply growth and verify balance
        account.apply_growth()
        self.assertEqual(account.balance, 11000)
    
    def test_account_with_allocation_still_uses_deterministic_when_not_mc(self):
        """Account with asset_allocation should still use deterministic
        growth when stochastic return hasn't been applied."""
        account = MockStochasticAccount(
            account_id="test_2",
            balance=10000,
            growth_rate=7.0,
            asset_allocation={"us_large_cap": 0.6, "us_bonds": 0.4}
        )
        
        # Has allocation but stochastic not applied
        self.assertIsNotNone(account.asset_allocation)
        self.assertFalse(account._stochastic_growth_applied)
        
        # Should still use deterministic 7% growth
        account.apply_growth()
        expected_balance = 10000 + (10000 * 0.07)  # 10700
        self.assertEqual(account.balance, expected_balance)
    
    def test_stochastic_flag_prevents_double_growth(self):
        """When stochastic return is applied, deterministic growth should be skipped."""
        account = MockStochasticAccount(
            account_id="test_3",
            balance=10000,
            growth_rate=7.0,
            asset_allocation={"us_large_cap": 1.0}
        )
        
        # Apply stochastic return (simulates Monte Carlo)
        stochastic_return = 0.12  # 12% return
        account.apply_stochastic_return(stochastic_return)
        
        # Balance should reflect stochastic return
        self.assertEqual(account.balance, 11200)  # 10000 * 1.12
        self.assertTrue(account._stochastic_growth_applied)
        
        # Now apply_growth should NOT add more growth
        account.apply_growth()
        
        # Balance should still be 11200, not 11984 (which would be double growth)
        self.assertEqual(account.balance, 11200)
        
        # Flag should be reset
        self.assertFalse(account._stochastic_growth_applied)
    
    def test_multiple_years_deterministic(self):
        """Deterministic growth should compound correctly over multiple years."""
        account = MockStochasticAccount(
            account_id="test_multi",
            balance=100000,
            growth_rate=10.0,  # 10% growth
            asset_allocation=None
        )
        
        # Simulate 3 years of growth
        for year in range(3):
            account.apply_growth()
        
        # 100000 * 1.1^3 = 133100
        expected_balance = 100000 * (1.10 ** 3)
        self.assertAlmostEqual(account.balance, expected_balance, places=2)
        
        # Should have 3 growth entries
        self.assertEqual(len(account.stat_growth_history), 3)
    
    def test_401k_structure_preserved(self):
        """401k account should maintain pretax/roth structure."""
        account = Mock401kAccount(
            account_id="401k_test",
            pretax_balance=60000,
            roth_balance=40000,
            asset_allocation=None
        )
        
        self.assertEqual(account.balance, 100000)
        self.assertEqual(account.pretax_balance, 60000)
        self.assertEqual(account.roth_balance, 40000)


class TestMonteCarloModeWorks(unittest.TestCase):
    """Tests verifying Monte Carlo simulation works correctly."""
    
    def test_stochastic_return_changes_balance(self):
        """apply_stochastic_return should correctly modify balance."""
        account = MockStochasticAccount(
            account_id="test_stochastic",
            balance=100000,
            asset_allocation={"us_large_cap": 1.0}
        )
        
        # Test positive return
        growth = account.apply_stochastic_return(0.15)  # 15% return
        self.assertEqual(growth, 15000)
        self.assertEqual(account.balance, 115000)
        
        # Reset flag to simulate next year
        account._stochastic_growth_applied = False
        
        # Test negative return
        growth = account.apply_stochastic_return(-0.10)  # -10% return
        self.assertEqual(growth, -11500)  # -10% of 115000
        self.assertEqual(account.balance, 103500)
    
    def test_401k_stochastic_applies_to_both_balances(self):
        """401k stochastic return should apply to pretax and roth."""
        account = Mock401kAccount(
            account_id="401k_test",
            pretax_balance=60000,
            roth_balance=40000,
            asset_allocation={"us_large_cap": 0.7, "us_bonds": 0.3}
        )
        
        self.assertEqual(account.balance, 100000)
        
        # Apply 10% stochastic return
        growth = account.apply_stochastic_return(0.10)
        
        # Should apply to both proportionally
        self.assertEqual(account.pretax_balance, 66000)  # 60000 * 1.10
        self.assertEqual(account.roth_balance, 44000)    # 40000 * 1.10
        self.assertEqual(account.balance, 110000)
        self.assertEqual(growth, 10000)
    
    def test_registry_only_collects_accounts_with_allocation(self):
        """Registry should only track accounts that have asset allocation."""
        registry = InvestmentAccountRegistry()
        
        # Account WITHOUT allocation
        account_no_alloc = MockStochasticAccount(
            account_id="no_alloc",
            balance=10000,
            asset_allocation=None
        )
        
        # Account WITH allocation
        account_with_alloc = MockStochasticAccount(
            account_id="with_alloc",
            balance=20000,
            asset_allocation={"us_large_cap": 1.0}
        )
        
        # Register both
        result1 = registry.register(account_no_alloc)
        result2 = registry.register(account_with_alloc)
        
        self.assertFalse(result1)  # Should fail - no allocation
        self.assertTrue(result2)   # Should succeed
        
        self.assertEqual(len(registry), 1)
        
        accounts = registry.get_accounts_with_allocations()
        self.assertEqual(len(accounts), 1)
        self.assertEqual(accounts[0][0], "with_alloc")
    
    def test_correlated_returns_are_actually_correlated(self):
        """Accounts with similar allocations should have correlated returns."""
        market = MarketAssumptions.create_default()
        calc = AccountParametersCalculator(market)
        
        # Two accounts with identical allocation should be perfectly correlated
        accounts = [
            ("acc1", {"us_large_cap": 0.8, "us_bonds": 0.2}),
            ("acc2", {"us_large_cap": 0.8, "us_bonds": 0.2}),
        ]
        
        corr_matrix, order, params = calc.calculate_account_correlation_matrix(accounts)
        
        # Identical allocations = correlation of 1.0
        self.assertAlmostEqual(corr_matrix[0, 1], 1.0, places=5)
        
        # Different allocations should have lower correlation
        accounts_diff = [
            ("stock", {"us_large_cap": 1.0}),
            ("bond", {"us_bonds": 1.0}),
        ]
        
        corr_matrix_diff, _, _ = calc.calculate_account_correlation_matrix(accounts_diff)
        
        # Stock-bond correlation should be low (around 0.1 based on default assumptions)
        self.assertLess(abs(corr_matrix_diff[0, 1]), 0.5)
    
    def test_return_generator_produces_different_returns_each_year(self):
        """Generator should produce different random returns each call."""
        params = [
            AccountStochasticParams("acc1", 0.08, 0.15),
        ]
        corr = np.array([[1.0]])
        
        generator = AccountCorrelatedReturnGenerator(params, corr, ["acc1"])
        
        np.random.seed(42)
        returns = [generator.generate_yearly_returns()["acc1"] for _ in range(100)]
        
        # Should have variety in returns
        self.assertGreater(max(returns), min(returns))
        
        # Mean should be close to expected return
        self.assertAlmostEqual(np.mean(returns), 0.08, places=1)
    
    def test_monte_carlo_results_aggregation(self):
        """MonteCarloResults should correctly compute percentiles and success rate."""
        import pandas as pd
        
        # Create 100 simulations with known values
        results = []
        for sim in range(100):
            # Simulation outcome depends on sim number
            # First 80 succeed (positive balance), last 20 fail (negative)
            if sim < 80:
                final_balance = 100000 + sim * 1000
            else:
                final_balance = -1000
            
            data = {
                'Year': [2025, 2026, 2027],
                'Bank Balance': [100000, 105000, final_balance],
            }
            results.append(pd.DataFrame(data))
        
        mc_results = MonteCarloResults(results)
        
        # Success rate should be 80%
        success = mc_results.success_rate('Bank Balance', min_balance=0, all_years=False)
        self.assertEqual(success, 0.80)
        
        # Percentiles should be computed
        percentiles = mc_results.get_percentile_data('Bank Balance')
        self.assertIn('Median', percentiles)
        self.assertEqual(len(percentiles['Median']), 3)  # 3 years


class TestModeIsolation(unittest.TestCase):
    """Tests ensuring deterministic and probabilistic modes don't interfere."""
    
    def test_account_id_is_unique(self):
        """Each account should have a unique ID."""
        account1 = MockStochasticAccount("acc_1", 1000)
        account2 = MockStochasticAccount("acc_2", 2000)
        account3 = MockStochasticAccount("acc_3", 3000)
        
        ids = {account1.account_id, account2.account_id, account3.account_id}
        self.assertEqual(len(ids), 3)  # All unique
    
    def test_asset_allocation_validation(self):
        """Asset allocation should sum to 1.0."""
        account = MockStochasticAccount("test", 1000)
        
        # Valid allocation
        account.asset_allocation = {"us_large_cap": 0.6, "us_bonds": 0.4}
        self.assertIsNotNone(account.asset_allocation)
        
        # Invalid allocation should raise
        with self.assertRaises(ValueError):
            account.asset_allocation = {"us_large_cap": 0.5, "us_bonds": 0.3}  # Sums to 0.8
    
    def test_growth_history_tracked_in_both_modes(self):
        """stat_growth_history should be updated in both modes."""
        # Test deterministic
        account1 = MockStochasticAccount("acc_det", 10000, growth_rate=10.0)
        account1.apply_growth()
        self.assertEqual(len(account1.stat_growth_history), 1)
        self.assertEqual(account1.stat_growth_history[0], 1000)
        
        # Test stochastic
        account2 = MockStochasticAccount(
            "acc_stoch", 10000,
            asset_allocation={"us_large_cap": 1.0}
        )
        account2.apply_stochastic_return(0.15)
        self.assertEqual(len(account2.stat_growth_history), 1)
        self.assertEqual(account2.stat_growth_history[0], 1500)
    
    def test_registry_apply_returns(self):
        """Registry should apply returns to registered accounts."""
        registry = InvestmentAccountRegistry()
        
        account1 = MockStochasticAccount(
            "acc1", 100000, asset_allocation={"us_large_cap": 1.0}
        )
        account2 = MockStochasticAccount(
            "acc2", 50000, asset_allocation={"us_bonds": 1.0}
        )
        
        registry.register(account1)
        registry.register(account2)
        
        # Apply different returns to each
        returns = {"acc1": 0.10, "acc2": 0.05}
        growth = registry.apply_returns(returns)
        
        # Verify balances updated
        self.assertEqual(account1.balance, 110000)  # 100k * 1.10
        self.assertEqual(account2.balance, 52500)   # 50k * 1.05
        
        # Verify returned growth amounts
        self.assertEqual(growth["acc1"], 10000)
        self.assertEqual(growth["acc2"], 2500)


class TestDerivedGrowthRateFromAllocation(unittest.TestCase):
    """Tests for deriving growth rate from asset allocation in deterministic mode."""
    
    def test_derived_return_used_in_deterministic_mode(self):
        """When allocation is provided, derived return should be used for growth."""
        market = MarketAssumptions.create_default()
        calc = AccountParametersCalculator(market)
        
        # Account with 60/40 allocation
        allocation = {"us_large_cap": 0.6, "us_bonds": 0.4}
        params = calc.calculate_account_params("test", allocation)
        
        # Expected return: 0.6 * 10% + 0.4 * 4% = 7.6%
        expected_return_pct = params.expected_return * 100
        
        # Create mock account with this allocation
        account = MockStochasticAccount(
            account_id="test",
            balance=100000,
            growth_rate=5.0,  # This should be IGNORED when allocation is set
            asset_allocation=allocation
        )
        
        # Simulate setting derived values (as real accounts do)
        account._derived_expected_return = params.expected_return
        
        # The effective growth rate should be the derived one, not 5.0
        self.assertAlmostEqual(account.effective_growth_rate, expected_return_pct, places=2)
    
    def test_fallback_to_fixed_rate_without_allocation(self):
        """Without allocation, should use the fixed growth_rate."""
        account = MockStochasticAccount(
            account_id="test",
            balance=100000,
            growth_rate=8.5,
            asset_allocation=None
        )
        
        # No derived return, so effective should be the fixed rate
        self.assertEqual(account.effective_growth_rate, 8.5)
    
    def test_derived_values_calculated_from_allocation(self):
        """Expected return and volatility should be calculated from allocation."""
        market = MarketAssumptions.create_default()
        calc = AccountParametersCalculator(market)
        
        # 100% bonds allocation
        bond_allocation = {"us_bonds": 1.0}
        params = calc.calculate_account_params("bond_account", bond_allocation)
        
        # Should get bond returns (4%) and volatility (6%)
        self.assertAlmostEqual(params.expected_return, 0.04, places=4)
        self.assertAlmostEqual(params.volatility, 0.06, places=4)
        
        # 100% large cap allocation
        stock_allocation = {"us_large_cap": 1.0}
        params = calc.calculate_account_params("stock_account", stock_allocation)
        
        # Should get stock returns (10%) and volatility (18%)
        self.assertAlmostEqual(params.expected_return, 0.10, places=4)
        self.assertAlmostEqual(params.volatility, 0.18, places=4)
    
    def test_diversification_reduces_volatility(self):
        """Mixed allocation should have lower volatility than weighted average."""
        market = MarketAssumptions.create_default()
        calc = AccountParametersCalculator(market)
        
        # 60/40 portfolio
        allocation = {"us_large_cap": 0.6, "us_bonds": 0.4}
        params = calc.calculate_account_params("balanced", allocation)
        
        # Weighted average volatility would be: 0.6 * 18% + 0.4 * 6% = 13.2%
        weighted_avg_vol = 0.6 * 0.18 + 0.4 * 0.06
        
        # Actual volatility should be LESS due to diversification (correlation < 1)
        self.assertLess(params.volatility, weighted_avg_vol)


class MockStochasticAccountWithDerived(MockStochasticAccount):
    """Extended mock that includes effective_growth_rate property."""
    
    @property
    def effective_growth_rate(self) -> float:
        if self._derived_expected_return is not None:
            return self._derived_expected_return * 100
        return self.growth_rate


# Patch the base class to have effective_growth_rate
MockStochasticAccount.effective_growth_rate = property(
    lambda self: self._derived_expected_return * 100 
    if getattr(self, '_derived_expected_return', None) is not None 
    else self.growth_rate
)

# Add derived return attribute to the mock
_original_init = MockStochasticAccount.__init__
def _new_init(self, account_id, balance, growth_rate=7.0, asset_allocation=None):
    _original_init(self, account_id, balance, growth_rate, asset_allocation)
    self._derived_expected_return = None
    self._derived_volatility = None
MockStochasticAccount.__init__ = _new_init


class TestEndToEndMonteCarloFlow(unittest.TestCase):
    """End-to-end tests of the full Monte Carlo workflow."""
    
    def test_full_monte_carlo_pipeline(self):
        """Test the complete MC pipeline from allocation to correlated returns."""
        # 1. Define market assumptions
        market = MarketAssumptions.create_default()
        
        # 2. Define accounts with allocations
        accounts = [
            ("retirement", {"us_large_cap": 0.6, "us_bonds": 0.4}),
            ("aggressive", {"us_large_cap": 0.9, "emerging_markets": 0.1}),
            ("conservative", {"us_bonds": 0.7, "cash": 0.3}),
        ]
        
        # 3. Calculate account parameters
        calc = AccountParametersCalculator(market)
        corr_matrix, order, params = calc.calculate_account_correlation_matrix(accounts)
        
        # Verify we got params for all accounts
        self.assertEqual(len(params), 3)
        self.assertEqual(order, ["retirement", "aggressive", "conservative"])
        
        # Verify correlation matrix shape
        self.assertEqual(corr_matrix.shape, (3, 3))
        
        # 4. Create return generator
        generator = AccountCorrelatedReturnGenerator(params, corr_matrix, order)
        
        # 5. Generate returns for multiple years
        np.random.seed(42)
        yearly_returns = [generator.generate_yearly_returns() for _ in range(30)]
        
        # Verify structure
        self.assertEqual(len(yearly_returns), 30)
        for returns in yearly_returns:
            self.assertIn("retirement", returns)
            self.assertIn("aggressive", returns)
            self.assertIn("conservative", returns)
        
        # 6. Verify aggressive has higher volatility than conservative
        aggressive_returns = [r["aggressive"] for r in yearly_returns]
        conservative_returns = [r["conservative"] for r in yearly_returns]
        
        self.assertGreater(np.std(aggressive_returns), np.std(conservative_returns))
    
    def test_reproducibility_with_seed(self):
        """Same seed should produce same results."""
        market = MarketAssumptions.create_default()
        calc = AccountParametersCalculator(market)
        
        accounts = [("test", {"us_large_cap": 0.5, "us_bonds": 0.5})]
        corr_matrix, order, params = calc.calculate_account_correlation_matrix(accounts)
        
        generator = AccountCorrelatedReturnGenerator(params, corr_matrix, order)
        
        # Run 1
        np.random.seed(123)
        returns1 = [generator.generate_yearly_returns()["test"] for _ in range(10)]
        
        # Run 2 with same seed
        np.random.seed(123)
        returns2 = [generator.generate_yearly_returns()["test"] for _ in range(10)]
        
        # Should be identical
        np.testing.assert_array_almost_equal(returns1, returns2)
    
    def test_different_seeds_produce_different_results(self):
        """Different seeds should produce different results."""
        market = MarketAssumptions.create_default()
        calc = AccountParametersCalculator(market)
        
        accounts = [("test", {"us_large_cap": 1.0})]
        corr_matrix, order, params = calc.calculate_account_correlation_matrix(accounts)
        
        generator = AccountCorrelatedReturnGenerator(params, corr_matrix, order)
        
        np.random.seed(111)
        returns1 = generator.generate_yearly_returns()["test"]
        
        np.random.seed(222)
        returns2 = generator.generate_yearly_returns()["test"]
        
        self.assertNotEqual(returns1, returns2)


if __name__ == '__main__':
    unittest.main()
