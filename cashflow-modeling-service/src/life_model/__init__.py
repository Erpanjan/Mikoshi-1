# Copyright 2022 Spencer Williams
#
# Use of this source code is governed by an MIT license:
# https://github.com/sw23/life-model/blob/main/LICENSE

"""
Cashflow Analytics Engine

A comprehensive personal finance simulation framework for multi-year
cashflow projections with modeling of income, expenses, loans, accounts,
insurance, taxes, and more.

Example usage:
    from life_model import LifeModel, Family, Person, Spending, BankAccount, Job, Salary
    
    model = LifeModel(start_year=2025, end_year=2050)
    family = Family(model)
    person = Person(family=family, name='John', age=30, retirement_age=65,
                    spending=Spending(model, base=30000))
    BankAccount(owner=person, company='Bank', type='Checking', balance=20000)
    Job(owner=person, company='Company', role='Employee',
        salary=Salary(model, base=75000, yearly_increase=3))
    
    model.run()
    df = model.get_yearly_stat_df()
"""

# Core simulation
from .model import LifeModel, Event, EventLog

# People
from .people.family import Family
from .people.person import Person, Spending

# Accounts
from .account.bank import BankAccount
from .account.job401k import Job401kAccount
from .account.brokerage import BrokerageAccount
from .account.hsa import HealthSavingsAccount
from .account.roth_IRA import RothIRA
from .account.traditional_IRA import TraditionalIRA

# Work
from .work.job import Job, Salary

# Debt
from .debt.student_loan import StudentLoan
from .debt.car_loan import CarLoan
from .debt.credit_card import CreditCard

# Insurance
from .insurance.life_insurance import LifeInsurance, LifeInsuranceType
from .insurance.social_security import SocialSecurity
from .insurance.general_insurance import Insurance, InsuranceType
from .insurance.annuity import Annuity

# Housing
from .housing.home import Home, Mortgage, HomeExpenses
from .housing.apartment import Apartment

# Life Events
from .lifeevents import LifeEvents, LifeEvent

# Monte Carlo Simulation
from .montecarlo import (
    MonteCarloSimulator,
    MonteCarloConfig,
    MonteCarloResults,
    MarketAssumptions,
    AssetClassAssumptions,
    AccountParametersCalculator,
    AccountStochasticParams,
    AccountCorrelatedReturnGenerator,
    InvestmentAccountRegistry,
)

# Version
from .__meta__ import __version__

__all__ = [
    # Core
    'LifeModel', 'Event', 'EventLog',
    # People
    'Family', 'Person', 'Spending',
    # Accounts
    'BankAccount', 'Job401kAccount', 'BrokerageAccount', 
    'HealthSavingsAccount', 'RothIRA', 'TraditionalIRA',
    # Work
    'Job', 'Salary',
    # Debt
    'StudentLoan', 'CarLoan', 'CreditCard',
    # Insurance
    'LifeInsurance', 'LifeInsuranceType', 'SocialSecurity', 
    'Insurance', 'InsuranceType', 'Annuity',
    # Housing
    'Home', 'Mortgage', 'HomeExpenses', 'Apartment',
    # Life Events
    'LifeEvents', 'LifeEvent',
    # Monte Carlo
    'MonteCarloSimulator', 'MonteCarloConfig', 'MonteCarloResults',
    'MarketAssumptions', 'AssetClassAssumptions',
    'AccountParametersCalculator', 'AccountStochasticParams',
    'AccountCorrelatedReturnGenerator', 'InvestmentAccountRegistry',
    # Version
    '__version__',
]
