import numpy as np

from equilibrium_saa import EquilibriumSAA
import dynamic_saa as dyn_mod
from dynamic_saa import DynamicSAA
import inspect


def run_synthetic_case(num_assets=6, risk_target=0.12, seed=42):
    rng = np.random.default_rng(seed)

    # Asset names and clusters
    asset_names = [f"A{i+1}" for i in range(num_assets)]
    clusters = {name: ("Equities" if i < num_assets // 2 else "Fixed Income") for i, name in enumerate(asset_names)}
    # Ensure one liquidity asset for equilibrium liquidity handling
    liquidity_asset = asset_names[-1]
    clusters[liquidity_asset] = "Liquidity"

    # Market weights
    market_weights = rng.random(num_assets)
    market_weights /= market_weights.sum()

    # Expected returns
    expected_returns = rng.normal(loc=0.06, scale=0.04, size=num_assets)

    # Base covariance (Σ)
    rand = rng.normal(size=(num_assets, num_assets))
    cov_base = rand @ rand.T
    cov_base = cov_base / np.max(np.abs(cov_base)) * 0.04  # scale to reasonable vols
    cov_base += np.eye(num_assets) * 0.01

    # Active covariance (Σ̃): slightly higher risk than base
    rand2 = rng.normal(size=(num_assets, num_assets))
    cov_active = rand2 @ rand2.T
    cov_active = cov_active / np.max(np.abs(cov_active)) * 0.05
    cov_active += np.eye(num_assets) * 0.015

    # Equilibrium
    eq_model = EquilibriumSAA(
        market_weights=market_weights,
        asset_clusters=clusters,
        risk_target=risk_target,
        cov_matrix=cov_base,
        asset_names=asset_names,
    )
    eq_w = eq_model.optimize()

    # Dynamic
    # Debug: show which module file is imported and snippet before running optimize
    try:
        print("Dynamic module file:", dyn_mod.__file__)
        src_lines = inspect.getsource(dyn_mod).splitlines()
        print("Source snippet around optimize():")
        for i in range(160, 186):
            if i < len(src_lines):
                print(f"{i+1}: ", src_lines[i])
    except Exception as e:
        print("Debug print failed before optimize:", e)

    dyn_model = DynamicSAA(
        equilibrium_weights=eq_w,
        expected_returns=expected_returns,
        active_cov_matrix=cov_active,
        asset_clusters=clusters,
        asset_names=asset_names,
        risk_target=risk_target,
        base_cov_matrix=cov_base,
        market_weights=market_weights,
        ask_user_for_fallback=False,
    )
    dyn_w = dyn_model.optimize()

    print("Equilibrium sum:", eq_w.sum())
    print("Dynamic sum:", dyn_w.sum())
    print("Equilibrium risk:", np.sqrt(eq_w @ cov_base @ eq_w))
    print("Dynamic risk:", np.sqrt(dyn_w @ cov_base @ dyn_w))
    print("Tracking error:", np.sqrt((dyn_w - eq_w) @ cov_active @ (dyn_w - eq_w)))


if __name__ == "__main__":
    run_synthetic_case()


