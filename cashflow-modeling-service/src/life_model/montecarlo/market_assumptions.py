# Copyright 2025 Spencer Williams
#
# Use of this source code is governed by an MIT license:
# https://github.com/sw23/life-model/blob/main/LICENSE

"""
Market assumptions for asset classes - provided by internal team.

This module contains the MarketAssumptions class which holds return, volatility,
and correlation assumptions for asset classes. The asset class list is dynamic
and determined by what the client uses in their asset allocations.
"""

from dataclasses import dataclass
from typing import Dict, List
import numpy as np


@dataclass
class AssetClassAssumptions:
    """Return and volatility assumptions for a single asset class.
    
    Attributes:
        name: Asset class identifier (e.g., "us_large_cap")
        expected_return: Annual expected return as decimal (e.g., 0.10 for 10%)
        volatility: Annual standard deviation as decimal (e.g., 0.18 for 18%)
    """
    name: str
    expected_return: float
    volatility: float
    
    def __post_init__(self):
        if self.volatility < 0:
            raise ValueError(f"Volatility cannot be negative: {self.volatility}")


class MarketAssumptions:
    """Internal team-provided market assumptions for asset classes.
    
    Asset classes are dynamic - determined by what the client uses.
    Internal team provides return, volatility, and correlation for each.
    
    Example:
        >>> assumptions = MarketAssumptions.create_default()
        >>> print(assumptions.asset_class_order)
        ['us_large_cap', 'us_small_cap', ...]
        >>> print(assumptions.get_returns_vector())
        [0.10, 0.12, ...]
    """
    
    def __init__(self, 
                 asset_classes: Dict[str, AssetClassAssumptions],
                 correlation_matrix: np.ndarray,
                 asset_class_order: List[str]):
        """Initialize market assumptions.
        
        Args:
            asset_classes: Dict mapping asset class name to its assumptions
            correlation_matrix: NxN correlation matrix for asset classes
            asset_class_order: Order of asset classes in the correlation matrix
        
        Raises:
            ValueError: If matrix dimensions don't match or asset classes missing
        """
        self.asset_classes = asset_classes
        self.correlation_matrix = correlation_matrix
        self.asset_class_order = asset_class_order
        self._validate()
        self._covariance_matrix = self._compute_covariance_matrix()
    
    def _validate(self):
        """Validate that all inputs are consistent."""
        n = len(self.asset_class_order)
        
        if self.correlation_matrix.shape != (n, n):
            raise ValueError(
                f"Correlation matrix shape {self.correlation_matrix.shape} "
                f"doesn't match {n} asset classes"
            )
        
        missing = [name for name in self.asset_class_order 
                   if name not in self.asset_classes]
        if missing:
            raise ValueError(f"Asset classes missing from assumptions: {missing}")
        
        # Check correlation matrix is symmetric and has 1s on diagonal
        if not np.allclose(self.correlation_matrix, self.correlation_matrix.T):
            raise ValueError("Correlation matrix must be symmetric")
        
        if not np.allclose(np.diag(self.correlation_matrix), 1.0):
            raise ValueError("Correlation matrix diagonal must be 1.0")
    
    def _compute_covariance_matrix(self) -> np.ndarray:
        """Compute covariance matrix from correlation and volatilities.
        
        Cov = diag(sigma) @ Corr @ diag(sigma)
        """
        vols = np.array([self.asset_classes[name].volatility 
                         for name in self.asset_class_order])
        vol_diag = np.diag(vols)
        return vol_diag @ self.correlation_matrix @ vol_diag
    
    @property
    def covariance_matrix(self) -> np.ndarray:
        """Get the covariance matrix for asset classes."""
        return self._covariance_matrix
    
    def get_returns_vector(self) -> np.ndarray:
        """Get expected returns as numpy array in asset_class_order."""
        return np.array([self.asset_classes[name].expected_return 
                         for name in self.asset_class_order])
    
    def get_volatilities_vector(self) -> np.ndarray:
        """Get volatilities as numpy array in asset_class_order."""
        return np.array([self.asset_classes[name].volatility 
                         for name in self.asset_class_order])
    
    @classmethod
    def create_default(cls) -> 'MarketAssumptions':
        """Create default market assumptions with common asset classes.
        
        Returns:
            MarketAssumptions with typical asset class parameters based on
            historical data and common financial planning assumptions.
        """
        asset_classes = {
            "us_large_cap": AssetClassAssumptions("us_large_cap", 0.10, 0.18),
            "us_small_cap": AssetClassAssumptions("us_small_cap", 0.12, 0.22),
            "intl_developed": AssetClassAssumptions("intl_developed", 0.08, 0.20),
            "emerging_markets": AssetClassAssumptions("emerging_markets", 0.10, 0.28),
            "us_bonds": AssetClassAssumptions("us_bonds", 0.04, 0.06),
            "intl_bonds": AssetClassAssumptions("intl_bonds", 0.03, 0.08),
            "reits": AssetClassAssumptions("reits", 0.09, 0.20),
            "cash": AssetClassAssumptions("cash", 0.02, 0.01),
        }
        order = list(asset_classes.keys())
        
        # Default correlation matrix based on typical asset class relationships
        # Order: us_large_cap, us_small_cap, intl_developed, emerging_markets,
        #        us_bonds, intl_bonds, reits, cash
        corr = np.array([
            [1.00, 0.85, 0.75, 0.70, 0.10, 0.05, 0.60, 0.00],  # US Large Cap
            [0.85, 1.00, 0.70, 0.65, 0.05, 0.00, 0.65, 0.00],  # US Small Cap
            [0.75, 0.70, 1.00, 0.80, 0.15, 0.20, 0.55, 0.00],  # Intl Developed
            [0.70, 0.65, 0.80, 1.00, 0.10, 0.15, 0.50, 0.00],  # Emerging Markets
            [0.10, 0.05, 0.15, 0.10, 1.00, 0.70, 0.20, 0.30],  # US Bonds
            [0.05, 0.00, 0.20, 0.15, 0.70, 1.00, 0.15, 0.25],  # Intl Bonds
            [0.60, 0.65, 0.55, 0.50, 0.20, 0.15, 1.00, 0.05],  # REITs
            [0.00, 0.00, 0.00, 0.00, 0.30, 0.25, 0.05, 1.00],  # Cash
        ])
        
        return cls(asset_classes, corr, order)
