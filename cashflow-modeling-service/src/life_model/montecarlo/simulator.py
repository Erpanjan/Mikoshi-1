# Copyright 2025 Spencer Williams
#
# Use of this source code is governed by an MIT license:
# https://github.com/sw23/life-model/blob/main/LICENSE

"""
Monte Carlo simulation orchestrator.

This module provides the MonteCarloSimulator class which orchestrates
running multiple simulation iterations with correlated stochastic returns.
"""

from typing import Callable, Optional, TYPE_CHECKING
import numpy as np

from .config import MonteCarloConfig
from .market_assumptions import MarketAssumptions
from .account_parameters import AccountParametersCalculator
from .return_generator import AccountCorrelatedReturnGenerator
from .account_registry import InvestmentAccountRegistry
from .results import MonteCarloResults

if TYPE_CHECKING:
    from ..model import LifeModel


class MonteCarloSimulator:
    """Orchestrates Monte Carlo simulations at investment account level.
    
    This simulator runs multiple iterations of the LifeModel simulation,
    applying correlated stochastic returns to investment accounts based
    on their asset allocations and market assumptions.
    
    The workflow:
    1. Create a fresh model using the provided factory function
    2. Collect all investment accounts with asset allocations
    3. Calculate account-level correlations from asset allocations
    4. Generate correlated returns each simulation year
    5. Aggregate results across all simulations
    
    Example:
        >>> market = MarketAssumptions.create_default()
        >>> simulator = MonteCarloSimulator(
        ...     market_assumptions=market,
        ...     config=MonteCarloConfig(num_simulations=500)
        ... )
        >>> results = simulator.run(create_model_function)
        >>> print(f"Success rate: {results.success_rate():.1%}")
    """
    
    def __init__(self, 
                 market_assumptions: Optional[MarketAssumptions] = None,
                 config: Optional[MonteCarloConfig] = None):
        """Initialize the simulator.
        
        Args:
            market_assumptions: Internal team's market assumptions. If None,
                               uses default assumptions.
            config: Simulation configuration. If None, uses defaults.
        """
        self.market = market_assumptions or MarketAssumptions.create_default()
        self.config = config or MonteCarloConfig()
        self.param_calculator = AccountParametersCalculator(self.market)
    
    def run(self, model_factory: Callable[[], 'LifeModel']) -> MonteCarloResults:
        """Run Monte Carlo simulation.
        
        Args:
            model_factory: Callable that creates a fresh LifeModel instance
                          with investment accounts configured. This function
                          is called once per simulation iteration.
        
        Returns:
            MonteCarloResults containing aggregated simulation data
        """
        if self.config.random_seed is not None:
            np.random.seed(self.config.random_seed)
        
        all_results = []
        
        for sim_idx in range(self.config.num_simulations):
            # Create fresh model for this simulation
            model = model_factory()
            
            # Collect accounts with asset allocations
            registry = self._build_registry(model)
            accounts_with_alloc = registry.get_accounts_with_allocations()
            
            if accounts_with_alloc:
                # Calculate account correlation matrix from allocations
                corr_matrix, account_order, params = \
                    self.param_calculator.calculate_account_correlation_matrix(
                        accounts_with_alloc
                    )
                
                # Create return generator for this simulation
                return_gen = AccountCorrelatedReturnGenerator(
                    params, corr_matrix, account_order
                )
                
                # Set model to probabilistic mode
                model.set_simulation_mode('probabilistic', return_gen, registry)
            
            # Run simulation
            model.run()
            
            # Collect results
            df = model.datacollector.get_model_vars_dataframe()
            all_results.append(df)
        
        return MonteCarloResults(all_results)
    
    def _build_registry(self, model: 'LifeModel') -> InvestmentAccountRegistry:
        """Build registry of investment accounts from model.
        
        Args:
            model: LifeModel instance to scan for investment accounts
        
        Returns:
            Registry containing all accounts with asset allocations
        """
        registry = InvestmentAccountRegistry()
        
        for agent in model.agents:
            # Check if agent is an investment account with stochastic support
            if hasattr(agent, 'asset_allocation') and hasattr(agent, 'account_id'):
                registry.register(agent)
        
        return registry
    
    def run_single(self, model_factory: Callable[[], 'LifeModel']) -> 'LifeModel':
        """Run a single probabilistic simulation and return the model.
        
        Useful for debugging or detailed analysis of a single run.
        
        Args:
            model_factory: Callable that creates a fresh LifeModel instance
        
        Returns:
            The LifeModel after running the simulation
        """
        if self.config.random_seed is not None:
            np.random.seed(self.config.random_seed)
        
        model = model_factory()
        
        registry = self._build_registry(model)
        accounts_with_alloc = registry.get_accounts_with_allocations()
        
        if accounts_with_alloc:
            corr_matrix, account_order, params = \
                self.param_calculator.calculate_account_correlation_matrix(
                    accounts_with_alloc
                )
            
            return_gen = AccountCorrelatedReturnGenerator(
                params, corr_matrix, account_order
            )
            
            model.set_simulation_mode('probabilistic', return_gen, registry)
        
        model.run()
        return model
