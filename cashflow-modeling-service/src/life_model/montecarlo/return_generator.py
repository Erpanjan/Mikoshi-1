# Copyright 2025 Spencer Williams
#
# Use of this source code is governed by an MIT license:
# https://github.com/sw23/life-model/blob/main/LICENSE

"""
Correlated return generator for investment accounts.

This module generates correlated random returns at the investment account level
using Cholesky decomposition. The correlation between accounts is derived from
their asset allocations.
"""

from typing import Dict, List
import numpy as np

from .account_parameters import AccountStochasticParams


class AccountCorrelatedReturnGenerator:
    """Generates correlated returns at the investment account level.
    
    Uses Cholesky decomposition to generate correlated normal random variables,
    then transforms them to account returns using each account's expected return
    and volatility.
    
    Example:
        >>> params = [
        ...     AccountStochasticParams("acc1", 0.08, 0.15),
        ...     AccountStochasticParams("acc2", 0.06, 0.10),
        ... ]
        >>> corr = np.array([[1.0, 0.7], [0.7, 1.0]])
        >>> gen = AccountCorrelatedReturnGenerator(params, corr, ["acc1", "acc2"])
        >>> returns = gen.generate_yearly_returns()
        >>> print(returns)  # e.g., {'acc1': 0.12, 'acc2': 0.04}
    """
    
    def __init__(self, 
                 account_params: List[AccountStochasticParams],
                 account_correlation_matrix: np.ndarray,
                 account_order: List[str]):
        """Initialize the return generator.
        
        Args:
            account_params: List of stochastic parameters for each account
            account_correlation_matrix: MxM correlation matrix between accounts
            account_order: List of account IDs in the same order as the matrix
        
        Raises:
            ValueError: If matrix is not positive definite
        """
        self.account_params = {p.account_id: p for p in account_params}
        self.account_order = account_order
        self.correlation_matrix = account_correlation_matrix
        
        # Cholesky decomposition for correlated sampling
        # L such that L @ L^T = correlation_matrix
        try:
            self._cholesky = np.linalg.cholesky(account_correlation_matrix)
        except np.linalg.LinAlgError as e:
            raise ValueError(
                "Correlation matrix is not positive definite. "
                "This may occur with certain allocation combinations."
            ) from e
    
    def generate_yearly_returns(self) -> Dict[str, float]:
        """Generate one year of correlated returns for all accounts.
        
        Returns:
            Dict mapping account_id to annual return for this simulation year.
            Returns are in decimal form (e.g., 0.08 for 8% return).
        """
        n = len(self.account_order)
        if n == 0:
            return {}
        
        # Generate uncorrelated standard normal samples
        uncorrelated_z = np.random.standard_normal(n)
        
        # Transform to correlated samples using Cholesky: z_corr = L @ z_uncorr
        correlated_z = self._cholesky @ uncorrelated_z
        
        # Transform to account returns: R_i = mu_i + sigma_i * z_i
        returns = {}
        for i, account_id in enumerate(self.account_order):
            params = self.account_params[account_id]
            returns[account_id] = params.expected_return + params.volatility * correlated_z[i]
        
        return returns
    
    def generate_multi_year_returns(self, num_years: int) -> List[Dict[str, float]]:
        """Generate multiple years of correlated returns.
        
        Args:
            num_years: Number of years to generate returns for
        
        Returns:
            List of yearly return dictionaries
        """
        return [self.generate_yearly_returns() for _ in range(num_years)]
