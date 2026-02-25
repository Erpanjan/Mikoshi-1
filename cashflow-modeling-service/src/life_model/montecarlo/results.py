# Copyright 2025 Spencer Williams
#
# Use of this source code is governed by an MIT license:
# https://github.com/sw23/life-model/blob/main/LICENSE

"""
Monte Carlo simulation results aggregation and analysis.

This module provides the MonteCarloResults class for analyzing the results
of Monte Carlo simulations, including percentile calculations and success rates.
"""

from typing import List, Dict, Optional
import pandas as pd
import numpy as np


class MonteCarloResults:
    """Aggregates and analyzes Monte Carlo simulation results.
    
    Provides methods to compute percentile bands, success rates, and other
    statistics across multiple simulation runs.
    
    Example:
        >>> results = MonteCarloResults(simulation_dataframes)
        >>> print(f"Success rate: {results.success_rate():.1%}")
        >>> percentiles = results.get_percentile_data('Bank Balance')
        >>> print(percentiles['Median'])
    """
    
    # Standard percentile levels for analysis
    PERCENTILES = {
        "Top 5%": 0.95,
        "Top 10%": 0.90,
        "Top 25%": 0.75,
        "Median": 0.50,
        "Bottom 25%": 0.25,
        "Bottom 10%": 0.10,
        "Bottom 5%": 0.05,
    }
    
    def __init__(self, simulation_results: List[pd.DataFrame]):
        """Initialize with simulation results.
        
        Args:
            simulation_results: List of DataFrames, one per simulation run.
                               Each DataFrame should have 'Year' column and
                               financial metrics as other columns.
        """
        self.raw_results = simulation_results
        self.num_simulations = len(simulation_results)
        
        if self.num_simulations > 0:
            self._num_years = len(simulation_results[0])
            self._years = simulation_results[0]['Year'].tolist() if 'Year' in simulation_results[0].columns else list(range(self._num_years))
        else:
            self._num_years = 0
            self._years = []
    
    def get_percentile_data(self, column: str = 'Bank Balance') -> Dict[str, List[float]]:
        """Get percentile bands for a specific metric across years.
        
        Args:
            column: Name of the column to analyze (e.g., 'Bank Balance', 
                   '401k Balance', 'Useable Balance')
        
        Returns:
            Dict mapping percentile names to lists of values (one per year)
        
        Raises:
            ValueError: If column not found in results
        """
        if self.num_simulations == 0:
            return {name: [] for name in self.PERCENTILES}
        
        if column not in self.raw_results[0].columns:
            available = list(self.raw_results[0].columns)
            raise ValueError(f"Column '{column}' not found. Available: {available}")
        
        percentile_data = {name: [] for name in self.PERCENTILES}
        
        for year_idx in range(self._num_years):
            yearly_values = [sim.iloc[year_idx][column] for sim in self.raw_results]
            yearly_values.sort()
            
            for name, pct in self.PERCENTILES.items():
                idx = int(self.num_simulations * pct)
                idx = min(idx, len(yearly_values) - 1)
                percentile_data[name].append(yearly_values[idx])
        
        return percentile_data
    
    def get_percentile_df(self, column: str = 'Bank Balance') -> pd.DataFrame:
        """Get percentile data as a DataFrame with years as index.
        
        Args:
            column: Name of the column to analyze
        
        Returns:
            DataFrame with years as index and percentile names as columns
        """
        percentile_data = self.get_percentile_data(column)
        df = pd.DataFrame(percentile_data)
        df['Year'] = self._years
        df = df.set_index('Year')
        return df
    
    def success_rate(self, 
                     column: str = 'Bank Balance',
                     min_balance: float = 0,
                     all_years: bool = True) -> float:
        """Calculate success rate of simulations.
        
        Args:
            column: Column to check for success condition
            min_balance: Minimum balance threshold for success
            all_years: If True, success requires min_balance in ALL years.
                      If False, only checks final year.
        
        Returns:
            Success rate as decimal (0.0 to 1.0)
        """
        if self.num_simulations == 0:
            return 0.0
        
        successful = 0
        for sim in self.raw_results:
            if all_years:
                # Success if balance >= threshold in all years
                is_successful = sim[column].min() >= min_balance
            else:
                # Success if final balance >= threshold
                is_successful = sim[column].iloc[-1] >= min_balance
            
            if is_successful:
                successful += 1
        
        return successful / self.num_simulations
    
    def get_years(self) -> List[int]:
        """Get list of years from simulation.
        
        Returns:
            List of year values
        """
        return self._years.copy()
    
    def get_final_values(self, column: str = 'Bank Balance') -> np.ndarray:
        """Get final year values from all simulations.
        
        Args:
            column: Column to extract
        
        Returns:
            numpy array of final values from each simulation
        """
        if self.num_simulations == 0:
            return np.array([])
        
        return np.array([sim[column].iloc[-1] for sim in self.raw_results])
    
    def get_statistics(self, column: str = 'Bank Balance', year_idx: int = -1) -> Dict[str, float]:
        """Get summary statistics for a specific year.
        
        Args:
            column: Column to analyze
            year_idx: Year index (-1 for final year, 0 for first year)
        
        Returns:
            Dict with mean, std, min, max, and percentile values
        """
        if self.num_simulations == 0:
            return {}
        
        values = np.array([sim[column].iloc[year_idx] for sim in self.raw_results])
        
        return {
            'mean': float(np.mean(values)),
            'std': float(np.std(values)),
            'min': float(np.min(values)),
            'max': float(np.max(values)),
            'p5': float(np.percentile(values, 5)),
            'p25': float(np.percentile(values, 25)),
            'p50': float(np.percentile(values, 50)),
            'p75': float(np.percentile(values, 75)),
            'p95': float(np.percentile(values, 95)),
        }
    
    def get_available_columns(self) -> List[str]:
        """Get list of available columns in results.
        
        Returns:
            List of column names
        """
        if self.num_simulations == 0:
            return []
        return list(self.raw_results[0].columns)
    
    def __repr__(self) -> str:
        return (f"MonteCarloResults(num_simulations={self.num_simulations}, "
                f"num_years={self._num_years})")
