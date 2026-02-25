from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import pandas as pd

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "layers.L1"

from layers.layer_types import Layer1Config, Layer1Result


def _prepare_sys_path(saa_model_dir: Path) -> None:
    """Ensure the SAA model directory is on sys.path for dynamic imports."""
    saa_model_dir = saa_model_dir.resolve()
    if str(saa_model_dir) not in sys.path:
        sys.path.append(str(saa_model_dir))


def run_layer1(config: Layer1Config) -> Layer1Result:
    """
    Execute Strategic Asset Allocation pipeline and return processed results.
    """
    saa_model_dir = Path(__file__).resolve().parent / "SAA Model"
    _prepare_sys_path(saa_model_dir)

    from main import run_saa_optimization  # type: ignore  # Imported dynamically

    data_file = Path(config.data_file).resolve()
    output_file_path: Optional[str] = None
    if config.export_excel:
        output_file = Path(config.output_file).resolve()
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file_path = str(output_file)

    results, saa_data = run_saa_optimization(
        data_file_path=str(data_file),
        output_file_path=output_file_path,
        risk_profile=config.risk_profile,
        target_volatility=config.target_volatility,
        export_excel_results=config.export_excel,
    )

    profile = config.risk_profile
    if profile not in results:
        available = ", ".join(results.keys())
        raise ValueError(f"Risk profile '{profile}' not found in SAA results. Available profiles: {available}")

    profile_results = results[profile]
    asset_classes = pd.Index(saa_data["asset_classes"])

    eq_weights = pd.Series(
        profile_results["equilibrium"]["weights"],
        index=asset_classes,
        name="equilibrium_weight",
    )

    dyn_weights: Optional[pd.Series] = None
    if "dynamic" in profile_results and "weights" in profile_results["dynamic"]:
        dyn_weights = pd.Series(
            profile_results["dynamic"]["weights"],
            index=asset_classes,
            name="dynamic_weight",
        )

    weight_type = config.weight_type.lower()
    if weight_type not in {"dynamic", "equilibrium"}:
        raise ValueError("weight_type must be either 'dynamic' or 'equilibrium'.")

    if weight_type == "dynamic":
        selected = dyn_weights if dyn_weights is not None else eq_weights
    else:
        selected = eq_weights

    target_vol = profile_results["target_vol"]
    asset_clusters = dict(saa_data["asset_clusters"])

    return Layer1Result(
        profile_name=profile,
        target_vol=target_vol,
        equilibrium_weights=eq_weights,
        dynamic_weights=dyn_weights,
        selected_weights=selected,
        asset_clusters=asset_clusters,
        raw_results=results,
        saa_data=saa_data,
    )
