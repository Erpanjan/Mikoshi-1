# Copyright 2025 Spencer Williams
#
# Use of this source code is governed by an MIT license:
# https://github.com/sw23/life-model/blob/main/LICENSE

"""
Tests for Monte Carlo simulation module.
"""

import unittest
import numpy as np
from unittest.mock import Mock, patch

from ..montecarlo.config import MonteCarloConfig
from ..montecarlo.market_assumptions import MarketAssumptions, AssetClassAssumptions
from ..montecarlo.account_parameters import AccountParametersCalculator, AccountStochasticParams
from ..montecarlo.return_generator import AccountCorrelatedReturnGenerator
from ..montecarlo.account_registry import InvestmentAccountRegistry
from ..montecarlo.results import MonteCarloResults
from ..montecarlo.simulator import MonteCarloSimulator


class TestMonteCarloConfig(unittest.TestCase):
    """Tests for MonteCarloConfig."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = MonteCarloConfig()
        self.assertEqual(config.num_simulations, 500)
        self.assertIsNone(config.random_seed)
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = MonteCarloConfig(num_simulations=1000, random_seed=42)
        self.assertEqual(config.num_simulations, 1000)
        self.assertEqual(config.random_seed, 42)
    
    def test_invalid_num_simulations(self):
        """Test that invalid num_simulations raises error."""
        with self.assertRaises(ValueError):
            MonteCarloConfig(num_simulations=0)
        with self.assertRaises(ValueError):
            MonteCarloConfig(num_simulations=-1)


class TestAssetClassAssumptions(unittest.TestCase):
    """Tests for AssetClassAssumptions."""
    
    def test_basic_creation(self):
        """Test basic asset class creation."""
        asset = AssetClassAssumptions("us_large_cap", 0.10, 0.18)
        self.assertEqual(asset.name, "us_large_cap")
        self.assertEqual(asset.expected_return, 0.10)
        self.assertEqual(asset.volatility, 0.18)
    
    def test_negative_volatility_raises(self):
        """Test that negative volatility raises error."""
        with self.assertRaises(ValueError):
            AssetClassAssumptions("test", 0.10, -0.05)


class TestMarketAssumptions(unittest.TestCase):
    """Tests for MarketAssumptions."""
    
    def test_create_default(self):
        """Test creating default market assumptions."""
        market = MarketAssumptions.create_default()
        
        # Check that we have the expected asset classes
        self.assertIn("us_large_cap", market.asset_classes)
        self.assertIn("us_bonds", market.asset_classes)
        self.assertIn("cash", market.asset_classes)
        
        # Check order matches
        self.assertEqual(len(market.asset_class_order), 8)
        
        # Check correlation matrix shape
        self.assertEqual(market.correlation_matrix.shape, (8, 8))
        
        # Check covariance matrix is computed
        self.assertEqual(market.covariance_matrix.shape, (8, 8))
    
    def test_get_returns_vector(self):
        """Test getting returns as vector."""
        market = MarketAssumptions.create_default()
        returns = market.get_returns_vector()
        
        self.assertEqual(len(returns), 8)
        # US large cap should have 10% return
        self.assertEqual(returns[0], 0.10)
    
    def test_get_volatilities_vector(self):
        """Test getting volatilities as vector."""
        market = MarketAssumptions.create_default()
        vols = market.get_volatilities_vector()
        
        self.assertEqual(len(vols), 8)
        # US large cap should have 18% volatility
        self.assertEqual(vols[0], 0.18)
    
    def test_invalid_correlation_matrix_shape(self):
        """Test that invalid correlation matrix shape raises error."""
        asset_classes = {
            "a": AssetClassAssumptions("a", 0.10, 0.18),
            "b": AssetClassAssumptions("b", 0.08, 0.15),
        }
        wrong_shape_matrix = np.array([[1.0]])  # Should be 2x2
        
        with self.assertRaises(ValueError):
            MarketAssumptions(asset_classes, wrong_shape_matrix, ["a", "b"])
    
    def test_asymmetric_correlation_matrix_raises(self):
        """Test that asymmetric correlation matrix raises error."""
        asset_classes = {
            "a": AssetClassAssumptions("a", 0.10, 0.18),
            "b": AssetClassAssumptions("b", 0.08, 0.15),
        }
        asymmetric = np.array([[1.0, 0.5], [0.3, 1.0]])  # Not symmetric
        
        with self.assertRaises(ValueError):
            MarketAssumptions(asset_classes, asymmetric, ["a", "b"])


class TestAccountParametersCalculator(unittest.TestCase):
    """Tests for AccountParametersCalculator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.market = MarketAssumptions.create_default()
        self.calculator = AccountParametersCalculator(self.market)
    
    def test_calculate_single_asset_account(self):
        """Test calculating params for account with single asset class."""
        allocation = {"us_large_cap": 1.0}
        params = self.calculator.calculate_account_params("test_account", allocation)
        
        self.assertEqual(params.account_id, "test_account")
        # 100% US large cap: return should be 10%
        self.assertAlmostEqual(params.expected_return, 0.10, places=6)
        # 100% US large cap: volatility should be 18%
        self.assertAlmostEqual(params.volatility, 0.18, places=6)
    
    def test_calculate_60_40_portfolio(self):
        """Test calculating params for 60/40 portfolio."""
        allocation = {"us_large_cap": 0.6, "us_bonds": 0.4}
        params = self.calculator.calculate_account_params("test_account", allocation)
        
        # Expected return: 0.6 * 10% + 0.4 * 4% = 7.6%
        expected_return = 0.6 * 0.10 + 0.4 * 0.04
        self.assertAlmostEqual(params.expected_return, expected_return, places=6)
        
        # Volatility should be less than weighted average due to diversification
        weighted_avg_vol = 0.6 * 0.18 + 0.4 * 0.06
        self.assertLess(params.volatility, weighted_avg_vol)
    
    def test_calculate_correlation_matrix_identical_accounts(self):
        """Test that identical accounts have correlation of 1.0."""
        allocation = {"us_large_cap": 0.6, "us_bonds": 0.4}
        accounts = [
            ("acc1", allocation.copy()),
            ("acc2", allocation.copy()),
        ]
        
        corr_matrix, order, params = self.calculator.calculate_account_correlation_matrix(accounts)
        
        self.assertEqual(order, ["acc1", "acc2"])
        # Identical portfolios should have correlation 1.0
        self.assertAlmostEqual(corr_matrix[0, 1], 1.0, places=6)
        self.assertAlmostEqual(corr_matrix[1, 0], 1.0, places=6)
    
    def test_calculate_correlation_matrix_different_accounts(self):
        """Test correlation between different allocations."""
        accounts = [
            ("stock_heavy", {"us_large_cap": 0.8, "us_bonds": 0.2}),
            ("bond_heavy", {"us_large_cap": 0.2, "us_bonds": 0.8}),
        ]
        
        corr_matrix, order, params = self.calculator.calculate_account_correlation_matrix(accounts)
        
        # Correlation should be between -1 and 1, but not 1.0 since allocations differ
        self.assertLess(corr_matrix[0, 1], 1.0)
        self.assertGreater(corr_matrix[0, 1], -1.0)


class TestAccountCorrelatedReturnGenerator(unittest.TestCase):
    """Tests for AccountCorrelatedReturnGenerator."""
    
    def test_generate_yearly_returns(self):
        """Test generating yearly returns."""
        params = [
            AccountStochasticParams("acc1", 0.08, 0.15),
            AccountStochasticParams("acc2", 0.06, 0.10),
        ]
        corr = np.array([[1.0, 0.7], [0.7, 1.0]])
        
        generator = AccountCorrelatedReturnGenerator(params, corr, ["acc1", "acc2"])
        
        np.random.seed(42)
        returns = generator.generate_yearly_returns()
        
        self.assertIn("acc1", returns)
        self.assertIn("acc2", returns)
        self.assertIsInstance(returns["acc1"], float)
        self.assertIsInstance(returns["acc2"], float)
    
    def test_returns_have_expected_statistics(self):
        """Test that generated returns have approximately correct mean/std over many samples."""
        params = [
            AccountStochasticParams("acc1", 0.08, 0.15),
        ]
        corr = np.array([[1.0]])
        
        generator = AccountCorrelatedReturnGenerator(params, corr, ["acc1"])
        
        np.random.seed(42)
        returns_list = [generator.generate_yearly_returns()["acc1"] for _ in range(10000)]
        
        mean_return = np.mean(returns_list)
        std_return = np.std(returns_list)
        
        # Mean should be close to expected return
        self.assertAlmostEqual(mean_return, 0.08, places=1)
        # Std should be close to volatility
        self.assertAlmostEqual(std_return, 0.15, places=1)
    
    def test_generate_multi_year_returns(self):
        """Test generating multiple years of returns."""
        params = [AccountStochasticParams("acc1", 0.08, 0.15)]
        corr = np.array([[1.0]])
        
        generator = AccountCorrelatedReturnGenerator(params, corr, ["acc1"])
        
        returns = generator.generate_multi_year_returns(5)
        
        self.assertEqual(len(returns), 5)
        for yearly_returns in returns:
            self.assertIn("acc1", yearly_returns)


class TestInvestmentAccountRegistry(unittest.TestCase):
    """Tests for InvestmentAccountRegistry."""
    
    def test_register_and_get(self):
        """Test registering and retrieving accounts."""
        registry = InvestmentAccountRegistry()
        
        # Create mock account
        account = Mock()
        account.account_id = "test_account"
        account.asset_allocation = {"us_large_cap": 1.0}
        
        result = registry.register(account)
        
        self.assertTrue(result)
        self.assertIn("test_account", registry)
        self.assertEqual(registry.get_account("test_account"), account)
    
    def test_register_without_allocation_fails(self):
        """Test that accounts without allocation are not registered."""
        registry = InvestmentAccountRegistry()
        
        account = Mock()
        account.account_id = "test_account"
        account.asset_allocation = None
        
        result = registry.register(account)
        
        self.assertFalse(result)
        self.assertNotIn("test_account", registry)
    
    def test_get_accounts_with_allocations(self):
        """Test getting all accounts with allocations."""
        registry = InvestmentAccountRegistry()
        
        account1 = Mock()
        account1.account_id = "acc1"
        account1.asset_allocation = {"us_large_cap": 0.6, "us_bonds": 0.4}
        
        account2 = Mock()
        account2.account_id = "acc2"
        account2.asset_allocation = {"us_bonds": 1.0}
        
        registry.register(account1)
        registry.register(account2)
        
        accounts = registry.get_accounts_with_allocations()
        
        self.assertEqual(len(accounts), 2)
        account_ids = [acc[0] for acc in accounts]
        self.assertIn("acc1", account_ids)
        self.assertIn("acc2", account_ids)
    
    def test_apply_returns(self):
        """Test applying returns to accounts."""
        registry = InvestmentAccountRegistry()
        
        account = Mock()
        account.account_id = "test_account"
        account.asset_allocation = {"us_large_cap": 1.0}
        account.apply_stochastic_return = Mock(return_value=1000.0)
        
        registry.register(account)
        
        growth = registry.apply_returns({"test_account": 0.10})
        
        account.apply_stochastic_return.assert_called_once_with(0.10)
        self.assertEqual(growth["test_account"], 1000.0)


class TestMonteCarloResults(unittest.TestCase):
    """Tests for MonteCarloResults."""
    
    def _create_sample_results(self, num_sims=10, num_years=5):
        """Create sample simulation results for testing."""
        import pandas as pd
        
        results = []
        for sim in range(num_sims):
            data = {
                'Year': list(range(2025, 2025 + num_years)),
                'Bank Balance': [100000 + sim * 1000 + year * 5000 for year in range(num_years)],
                '401k Balance': [50000 + sim * 500 + year * 2500 for year in range(num_years)],
            }
            results.append(pd.DataFrame(data))
        return results
    
    def test_percentile_data(self):
        """Test getting percentile data."""
        results = MonteCarloResults(self._create_sample_results())
        
        percentiles = results.get_percentile_data('Bank Balance')
        
        self.assertIn('Median', percentiles)
        self.assertIn('Top 5%', percentiles)
        self.assertIn('Bottom 5%', percentiles)
        
        # Each percentile should have values for each year
        self.assertEqual(len(percentiles['Median']), 5)
    
    def test_success_rate_all_successful(self):
        """Test success rate when all simulations succeed."""
        results = MonteCarloResults(self._create_sample_results())
        
        # All balances are positive, so success rate should be 100%
        rate = results.success_rate(column='Bank Balance', min_balance=0)
        
        self.assertEqual(rate, 1.0)
    
    def test_success_rate_partial(self):
        """Test success rate when some simulations fail."""
        import pandas as pd
        
        # Create results where some fail
        sample_results = []
        for sim in range(10):
            if sim < 3:
                # These will "fail" - balance goes negative
                balances = [-1000, -2000, -3000, -4000, -5000]
            else:
                balances = [100000, 110000, 120000, 130000, 140000]
            
            data = {
                'Year': list(range(2025, 2030)),
                'Bank Balance': balances,
            }
            sample_results.append(pd.DataFrame(data))
        
        results = MonteCarloResults(sample_results)
        rate = results.success_rate(column='Bank Balance', min_balance=0)
        
        # 7 out of 10 should succeed
        self.assertEqual(rate, 0.7)
    
    def test_get_years(self):
        """Test getting years from results."""
        results = MonteCarloResults(self._create_sample_results())
        
        years = results.get_years()
        
        self.assertEqual(years, [2025, 2026, 2027, 2028, 2029])
    
    def test_get_final_values(self):
        """Test getting final year values."""
        results = MonteCarloResults(self._create_sample_results())
        
        final_values = results.get_final_values('Bank Balance')
        
        self.assertEqual(len(final_values), 10)  # 10 simulations
    
    def test_get_statistics(self):
        """Test getting summary statistics."""
        results = MonteCarloResults(self._create_sample_results())
        
        stats = results.get_statistics('Bank Balance')
        
        self.assertIn('mean', stats)
        self.assertIn('std', stats)
        self.assertIn('min', stats)
        self.assertIn('max', stats)
        self.assertIn('p50', stats)


if __name__ == '__main__':
    unittest.main()
