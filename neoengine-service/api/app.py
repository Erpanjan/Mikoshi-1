"""
Flask web server for Neo-Engine portfolio optimization API.
"""

import os
import hashlib
import hmac
import threading
from pathlib import Path
from typing import Dict, Any, Tuple, List
from datetime import datetime, timedelta, timezone

from flask import Flask, request, jsonify
from google.cloud import storage
import requests

# Import the optimization pipeline
# Add parent directory to path to access SAA Model
import sys

# Get the project root (parent of api directory)
# This works whether running from api/ or from parent directory
_current_file = Path(__file__).resolve()
if _current_file.parent.name == "api":
    # Running from api directory - go up one level
    BASE_DIR = _current_file.parent.parent
else:
    # Running as module - already at correct level
    BASE_DIR = _current_file.parent.parent
SAA_MODEL_DIR = BASE_DIR / "SAA Model"

# Change to SAA Model directory for relative imports to work
_original_cwd = os.getcwd()
os.chdir(str(SAA_MODEL_DIR))
sys.path.insert(0, str(SAA_MODEL_DIR))

from layers.L2.layer2_active_risk import (
    run_layered_optimization,
    build_layer1_config,
    build_layer2_config,
    build_layer3_config,
    ActiveRiskAllocator,
)
from layers.L1.layer1_saa import run_layer1
from layers.L3.layer3_manager_selection import ManagerSelectionEngine
from layers.L3.portfolio_metrics import compute_portfolio_expected_return_and_volatility
import argparse

# Restore original working directory
os.chdir(_original_cwd)

app = Flask(__name__)

# Load environment variables
# Priority: 1) Process environment variables (Docker --env-file, GitHub Actions, etc.)
#           2) .env file (for local development)
# This allows GitHub Actions to pass env vars directly, while local dev uses .env file
try:
    from dotenv import load_dotenv

    # Only load .env if it exists and variables aren't already set
    # override=False ensures environment variables take precedence
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)
except ImportError:
    pass  # dotenv is optional

# Read from environment (works with both Docker env vars and .env file)
API_SECRET = os.getenv("API_SECRET")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
GCS_PROJECT_ID = os.getenv("GCS_PROJECT_ID")
GCS_CREDENTIALS_PATH = os.getenv("GCS_CREDENTIALS_PATH")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))
LOCAL_DEV = os.getenv("LOCAL_DEV", "false").lower() == "true"

# Validate required environment variables (skip in local dev mode)
if not LOCAL_DEV:
    if not API_SECRET:
        raise ValueError("API_SECRET environment variable is required")
    if not GCS_BUCKET_NAME:
        raise ValueError("GCS_BUCKET_NAME environment variable is required")
    if not GCS_PROJECT_ID:
        raise ValueError("GCS_PROJECT_ID environment variable is required")
else:
    print("Running in LOCAL_DEV mode - GCS disabled", file=sys.stderr, flush=True)
    API_SECRET = API_SECRET or "local-dev-secret"

# Initialize GCS client (skip in LOCAL_DEV mode)
storage_client = None
bucket = None

if LOCAL_DEV:
    print("Skipping GCS initialization in LOCAL_DEV mode", file=sys.stderr, flush=True)
else:
    try:
        print("Initializing GCS client...", file=sys.stderr, flush=True)

        # Resolve credentials path - try multiple locations
        credentials_path = None
        if GCS_CREDENTIALS_PATH:
            # Try as-is first
            if os.path.exists(GCS_CREDENTIALS_PATH):
                credentials_path = GCS_CREDENTIALS_PATH
            else:
                # Try relative to api directory
                api_dir = Path(__file__).parent
                potential_path = api_dir / GCS_CREDENTIALS_PATH
                if potential_path.exists():
                    credentials_path = str(potential_path)
                else:
                    # Try relative to app root
                    app_root = Path(__file__).parent.parent
                    potential_path = app_root / GCS_CREDENTIALS_PATH
                    if potential_path.exists():
                        credentials_path = str(potential_path)
        if credentials_path and os.path.exists(credentials_path):
            print(
                f"Using service account credentials from: {credentials_path}",
                file=sys.stderr,
                flush=True,
            )
            storage_client = storage.Client.from_service_account_json(
                credentials_path, project=GCS_PROJECT_ID
            )
        else:
            print(
                "Using default credentials (for Cloud Run or Application Default Credentials)",
                file=sys.stderr,
                flush=True,
            )
            if GCS_CREDENTIALS_PATH:
                print(
                    f"WARNING: Credentials file not found at: {GCS_CREDENTIALS_PATH}",
                    file=sys.stderr,
                    flush=True,
                )
            # Try to use default credentials (for Cloud Run)
            storage_client = storage.Client(project=GCS_PROJECT_ID)

        print(
            f"Creating bucket reference for: {GCS_BUCKET_NAME}", file=sys.stderr, flush=True
        )
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        print("GCS client initialized successfully!", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"ERROR: Could not initialize GCS client: {e}", file=sys.stderr, flush=True)
        import traceback

        traceback.print_exc(file=sys.stderr)
        print(
            "GCS operations will fail. Make sure credentials are properly configured.",
            file=sys.stderr,
            flush=True,
        )
        storage_client = None
        bucket = None


def verify_api_key(api_key: str) -> bool:
    """Verify API key using HMAC."""
    if not api_key:
        return False

    # API keys are stored as: HMAC(secret, "api_key")
    # We need to check if the provided key matches any valid key
    # For simplicity, we'll check against a single expected key
    # In production, you might want to store valid keys in a database

    # Generate expected key from secret
    expected_key = hmac.new(
        API_SECRET.encode("utf-8"), b"api_key", hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(api_key, expected_key)


def require_api_key(f):
    """Decorator to require API key authentication."""

    def decorated_function(*args, **kwargs):
        api_key = request.headers.get("X-Api-Key")
        if not api_key or not verify_api_key(api_key):
            return (
                jsonify(
                    {"error": "Unauthorized", "message": "Invalid or missing API key"}
                ),
                401,
            )
        return f(*args, **kwargs)

    decorated_function.__name__ = f.__name__
    return decorated_function


def upload_file_to_gcs(local_path: Path, gcs_path: str) -> str:
    """Upload a file to Google Cloud Storage and return presigned URL."""
    if not bucket or not storage_client:
        raise RuntimeError("GCS bucket not initialized. Check your GCS configuration.")

    blob = bucket.blob(gcs_path)
    blob.upload_from_filename(str(local_path))

    # Generate presigned URL (valid for 1 hour)
    # The client will automatically use the service account credentials
    url = blob.generate_signed_url(
        version="v4", expiration=timedelta(hours=1), method="GET"
    )
    return url


def call_webhook(webhook_config: Dict[str, Any], data: Dict[str, Any]) -> None:
    """Call webhook with provided configuration."""
    url = webhook_config.get("url")
    method = webhook_config.get("method", "POST")
    headers = webhook_config.get("headers", {})

    if method != "POST":
        # This should have been validated earlier, but double-check
        return

    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        response.raise_for_status()
    except Exception as e:
        # Log error but don't fail the request
        print(f"Webhook call failed: {e}")


def run_optimization(
    risk_profile: str = "RP1",
    weight_type: str = "dynamic",
    target_volatility: float = None,
    active_risk_percentage: float = None,
) -> Tuple[Path, Path]:
    """Run the portfolio optimization pipeline and return output file paths."""
    # Create a namespace for temporary outputs
    temp_output_dir = Path("/tmp/neo_outputs")
    temp_output_dir.mkdir(parents=True, exist_ok=True)

    saa_output = temp_output_dir / "SAA_Results.xlsx"
    portfolio_output = temp_output_dir / "Portfolio_Construction_Results.xlsx"

    # Build arguments
    args = argparse.Namespace(
        risk_profile=risk_profile,
        weight_type=weight_type,
        target_volatility=target_volatility,
        active_risk_percentage=active_risk_percentage,
    )

    # Temporarily modify the output paths in the config
    # We need to patch the config building functions
    import layers.L2.layer2_active_risk as layer2_module

    original_build_layer1_config = layer2_module.build_layer1_config
    original_build_layer2_config = layer2_module.build_layer2_config

    # Change to SAA Model directory for relative paths to work
    original_cwd = os.getcwd()
    saa_model_dir = BASE_DIR / "SAA Model"

    try:
        os.chdir(str(saa_model_dir))

        # Monkey patch to use temp outputs
        def patched_layer1_config(args):
            config = original_build_layer1_config(args)
            config.output_file = saa_output
            return config

        def patched_layer2_config(args, layer1_target_vol):
            config = original_build_layer2_config(args, layer1_target_vol)
            config.output_file = portfolio_output
            return config

        # Replace the functions temporarily
        layer2_module.build_layer1_config = patched_layer1_config
        layer2_module.build_layer2_config = patched_layer2_config

        # Run optimization
        run_layered_optimization(args)

        return saa_output, portfolio_output
    finally:
        # Restore original functions and working directory
        layer2_module.build_layer1_config = original_build_layer1_config
        layer2_module.build_layer2_config = original_build_layer2_config
        os.chdir(original_cwd)


def run_optimization_json(
    risk_profile: str = "RP3",
    target_volatility: float = 0.12,
    weight_type: str = "dynamic",
    investment_amount: float = None,
    active_risk_percentage: float = None,
) -> Dict[str, Any]:
    """
    Run the portfolio optimization pipeline and return results as JSON.

    This is a JSON-friendly version of run_layered_optimization that returns
    structured data instead of writing to Excel files.

    Args:
        risk_profile: Risk profile (RP1-RP5)
        target_volatility: Target portfolio volatility (e.g., 0.12 for 12%)
        weight_type: 'dynamic' or 'equilibrium'
        investment_amount: Optional total investment amount in dollars for calculating allocations
        active_risk_percentage: Optional Layer 2 active risk split (0.0-1.0)

    Returns:
        Dictionary with all three layers' results, portfolio summary, and investment allocations
    """
    # Build arguments
    args = argparse.Namespace(
        risk_profile=risk_profile,
        weight_type=weight_type,
        target_volatility=target_volatility,
        active_risk_percentage=active_risk_percentage,
    )

    # Change to SAA Model directory for relative paths to work
    original_cwd = os.getcwd()
    saa_model_dir = BASE_DIR / "SAA Model"

    try:
        os.chdir(str(saa_model_dir))

        # Build configurations
        # JSON optimize path is compute-only for Layer 1 (no Excel export side effects).
        layer1_config = build_layer1_config(args, export_excel=False)
        layer3_config = build_layer3_config()

        # Execute Layer 1: Strategic Asset Allocation
        layer1_result = run_layer1(layer1_config)

        # Build Layer 2 config using Layer 1's target volatility
        layer2_config = build_layer2_config(args, layer1_result.target_vol)

        # Execute Layer 2: Active Risk Allocation
        layer2_engine = ActiveRiskAllocator(layer2_config)
        (
            target_active_risks,
            active_alloc,
            achieved_vol,
            risk_budget_shares,
            layer2_info,
        ) = layer2_engine.run(layer1_result)

        # Execute Layer 3: Manager Selection
        manager_engine = ManagerSelectionEngine(layer3_config)
        manager_result = manager_engine.run(target_tes=target_active_risks)

        # Serialize results to JSON-compatible format
        # Layer 1 results
        layer1_json = {
            "profile_name": layer1_result.profile_name,
            "target_vol": float(layer1_result.target_vol),
            "equilibrium_weights": (
                layer1_result.equilibrium_weights.to_dict()
                if layer1_result.equilibrium_weights is not None
                else {}
            ),
            "dynamic_weights": (
                layer1_result.dynamic_weights.to_dict()
                if layer1_result.dynamic_weights is not None
                else None
            ),
            "selected_weights": (
                layer1_result.selected_weights.to_dict()
                if layer1_result.selected_weights is not None
                else {}
            ),
            "asset_clusters": layer1_result.asset_clusters,
        }

        # Layer 2 results
        layer2_json = {
            "target_active_risks": {
                k: float(v) for k, v in target_active_risks.items()
            },
            "active_allocations": {k: float(v) for k, v in active_alloc.items()},
            "achieved_volatility": float(achieved_vol),
            "risk_budget_shares": {k: float(v) for k, v in risk_budget_shares.items()},
            "active_risk_budget": float(layer2_info.get("active_risk_budget", 0.0)),
            "passive_risk_pct": float(layer2_info.get("passive_risk_pct", 0.0)),
            "active_risk_pct": float(layer2_info.get("active_risk_pct", 0.0)),
            "passive_tickers": layer2_info.get("passive_tickers", {}),
            "passive_names": layer2_info.get("passive_names", {}),
        }

        # Get manager details from manager_data for enrichment
        manager_data_df = manager_result.manager_data
        manager_lookup = {}
        if manager_data_df is not None and not manager_data_df.empty:
            for _, row in manager_data_df.iterrows():
                isin = row.get("ISIN", "")
                # Try different column names for fund name
                name = row.get("Name") or row.get("Manager Name") or row.get("Fund Name") or isin
                manager_lookup[isin] = {
                    "name": name,
                    "ticker": row.get("Ticker", ""),
                    "asset_class": row.get("AssetClass", ""),
                    "expected_te": float(row.get("Expected Tracking Error", 0)),
                    "expected_ir": float(row.get("Expected Information Ratio", 0)),
                }

        # Layer 3 results with enriched security details
        layer3_json = {
            "allocations_by_asset_class": {
                asset_class: {
                    manager: float(weight) for manager, weight in managers.items()
                }
                for asset_class, managers in manager_result.allocations.items()
            },
            "securities": [
                {
                    "isin": isin,
                    "name": manager_lookup.get(isin, {}).get("name", isin),
                    "ticker": manager_lookup.get(isin, {}).get("ticker", ""),
                    "asset_class": asset_class,
                    "weight_in_asset_class": float(weight),
                    "expected_te": manager_lookup.get(isin, {}).get("expected_te", 0),
                    "expected_ir": manager_lookup.get(isin, {}).get("expected_ir", 0),
                }
                for asset_class, managers in manager_result.allocations.items()
                for isin, weight in managers.items()
            ],
            "active_volatilities": {
                k: float(v) for k, v in manager_result.active_vols.items()
            },
            "active_tracking_errors": {
                k: float(v) for k, v in manager_result.active_tes.items()
            },
        }

        # Calculate portfolio summary
        total_managers = sum(
            len(managers) for managers in manager_result.allocations.values()
        )
        total_tracking_error = (
            sum(manager_result.active_tes.values())
            if manager_result.active_tes
            else 0.0
        )

        # Portfolio expected return/volatility are sourced from Layer 3 portfolio metrics.
        # This aligns API output with the SAA model documentation.
        passive_vols = layer2_info.get("passive_vols", {}) or {}
        portfolio_expected_return, portfolio_expected_volatility = (
            compute_portfolio_expected_return_and_volatility(
                layer1_result=layer1_result,
                active_allocations=active_alloc,
                manager_result=manager_result,
                passive_vols=passive_vols,
            )
        )

        portfolio_summary = {
            "total_volatility": float(portfolio_expected_volatility),
            "total_tracking_error": float(total_tracking_error),
            "expected_return": float(portfolio_expected_return),
            "manager_count": total_managers,
            "asset_class_count": len(layer1_result.selected_weights),
            "achieved_volatility_layer2": float(achieved_vol),
        }

        normalized_total_investment = (
            float(investment_amount) if isinstance(investment_amount, (int, float)) and investment_amount > 0 else None
        )

        # Canonical unified security list:
        # - passive sleeve security from Layer 2 per asset class
        # - active sleeve securities from Layer 3 managers
        # Every row uses portfolio-level weight and amount.
        unified_securities: List[Dict[str, Any]] = []
        selected_weights = layer1_result.selected_weights.to_dict()
        active_allocations = active_alloc
        passive_tickers = layer2_info.get("passive_tickers", {}) or {}

        # Passive sleeve rows
        for asset_class, asset_weight_raw in selected_weights.items():
            asset_weight = float(asset_weight_raw)
            alpha = float(active_allocations.get(asset_class, 0.0))
            alpha = max(0.0, min(1.0, alpha))
            passive_weight = asset_weight * (1.0 - alpha)
            if passive_weight <= 0:
                continue

            ticker = str(passive_tickers.get(asset_class, "") or "").strip()
            unified_securities.append(
                {
                    "isin": ticker or "",
                    "asset_class": str(asset_class),
                    "security_type": "passive",
                    "weight": float(passive_weight),
                    "amount": (
                        float(passive_weight * normalized_total_investment)
                        if normalized_total_investment is not None
                        else 0.0
                    ),
                }
            )

        # Active sleeve rows
        for asset_class, managers in manager_result.allocations.items():
            asset_weight = float(selected_weights.get(asset_class, 0.0))
            alpha = float(active_allocations.get(asset_class, 0.0))
            alpha = max(0.0, min(1.0, alpha))
            if asset_weight <= 0 or alpha <= 0:
                continue

            for isin, manager_weight_raw in managers.items():
                manager_weight = float(manager_weight_raw)
                total_weight = asset_weight * alpha * manager_weight
                if total_weight <= 0:
                    continue
                unified_securities.append(
                    {
                        "isin": str(isin or ""),
                        "asset_class": str(asset_class),
                        "security_type": "active",
                        "weight": float(total_weight),
                        "amount": (
                            float(total_weight * normalized_total_investment)
                            if normalized_total_investment is not None
                            else 0.0
                        ),
                    }
                )

        unified_securities.sort(key=lambda row: float(row.get("weight", 0.0)), reverse=True)

        # Keep detailed allocation blocks for compatibility/debugging.
        investment_allocations = {
            "total_investment": normalized_total_investment,
            "by_asset_class": {
                str(asset_class): {
                    "weight": float(weight),
                    "amount": (
                        float(float(weight) * normalized_total_investment)
                        if normalized_total_investment is not None
                        else 0.0
                    ),
                }
                for asset_class, weight in selected_weights.items()
            },
            "by_security": unified_securities,
        }

        # Build response
        response = {
            "success": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_investment": normalized_total_investment,
            "portfolio_expected_return_pct": float(portfolio_expected_return) * 100.0,
            "portfolio_expected_volatility_pct": float(portfolio_expected_volatility) * 100.0,
            "securities": unified_securities,
            "layers": {
                "layer1": layer1_json,
                "layer2": layer2_json,
                "layer3": layer3_json,
            },
            "portfolio_summary": portfolio_summary,
            "investment_allocations": investment_allocations,
        }

        return response

    except Exception as e:
        # Return error in JSON format
        return {
            "success": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "error_type": type(e).__name__,
        }
    finally:
        os.chdir(original_cwd)


@app.route("/neo/api/v1/generate", methods=["POST"])
@require_api_key
def generate():
    """Generate portfolio optimization results."""
    try:
        data = request.get_json() or {}

        # Validate required parameters
        storage_id = data.get("storageId")
        file_name = data.get("fileName")

        errors = {}
        if not storage_id:
            errors["storageId"] = [
                {"message": "storageId is required", "code": "REQUIRED"}
            ]
        if not file_name:
            errors["fileName"] = [
                {"message": "fileName is required", "code": "REQUIRED"}
            ]

        if errors:
            return jsonify(errors), 422

        # Validate webhook if provided
        webhook = data.get("webhook")
        if webhook:
            if not isinstance(webhook, dict):
                return jsonify({"error": "webhook must be an object"}), 400

            webhook_method = webhook.get("method", "POST")
            if webhook_method != "POST":
                return (
                    jsonify(
                        {
                            "error": "webhook method must be POST",
                            "code": "INVALID_METHOD",
                        }
                    ),
                    400,
                )

            if not webhook.get("url"):
                return (
                    jsonify({"error": "webhook url is required", "code": "REQUIRED"}),
                    400,
                )

        # Get optional optimization parameters
        risk_profile = data.get("riskProfile", "RP1")
        weight_type = data.get("weightType", "dynamic")

        # If webhook is provided, run asynchronously
        if webhook:

            def async_task():
                try:
                    # Run optimization
                    saa_path, portfolio_path = run_optimization(
                        risk_profile=risk_profile,
                        weight_type=weight_type,
                    )

                    # Upload to GCS
                    saa_gcs_path = f"{storage_id}/{file_name}/SAA_Results.xlsx"
                    portfolio_gcs_path = (
                        f"{storage_id}/{file_name}/Portfolio_Construction_Results.xlsx"
                    )

                    saa_url = upload_file_to_gcs(saa_path, saa_gcs_path)
                    portfolio_url = upload_file_to_gcs(
                        portfolio_path, portfolio_gcs_path
                    )

                    # Call webhook
                    webhook_data = {
                        "storageId": storage_id,
                        "fileName": file_name,
                        "status": "completed",
                        "files": {
                            "saaResults": saa_url,
                            "portfolioResults": portfolio_url,
                        },
                    }
                    call_webhook(webhook, webhook_data)

                    # Cleanup temp files
                    if saa_path.exists():
                        saa_path.unlink()
                    if portfolio_path.exists():
                        portfolio_path.unlink()
                except Exception as e:
                    # Call webhook with error
                    if webhook:
                        error_data = {
                            "storageId": storage_id,
                            "fileName": file_name,
                            "status": "error",
                            "error": str(e),
                        }
                        call_webhook(webhook, error_data)

            # Start async task
            thread = threading.Thread(target=async_task)
            thread.daemon = True
            thread.start()

            # Return immediately
            return (
                jsonify(
                    {
                        "status": "processing",
                        "message": "Request accepted and processing started",
                    }
                ),
                202,
            )

        else:
            # Synchronous execution
            saa_path, portfolio_path = run_optimization(
                risk_profile=risk_profile,
                weight_type=weight_type,
            )

            # Upload to GCS
            saa_gcs_path = f"{storage_id}/{file_name}/SAA_Results.xlsx"
            portfolio_gcs_path = (
                f"{storage_id}/{file_name}/Portfolio_Construction_Results.xlsx"
            )

            saa_url = upload_file_to_gcs(saa_path, saa_gcs_path)
            portfolio_url = upload_file_to_gcs(portfolio_path, portfolio_gcs_path)

            # Cleanup temp files
            if saa_path.exists():
                saa_path.unlink()
            if portfolio_path.exists():
                portfolio_path.unlink()

            return (
                jsonify(
                    {
                        "status": "completed",
                        "files": {
                            "saaResults": saa_url,
                            "portfolioResults": portfolio_url,
                        },
                    }
                ),
                200,
            )

    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500


@app.route("/neo/api/v1/optimize", methods=["POST"])
@require_api_key
def optimize():
    """
    Run portfolio optimization and return JSON results.

    This endpoint is designed for NestJS integration with Gemini function calling.
    Unlike /generate, this returns JSON directly without uploading to GCS.

    Request body:
    {
        "risk_profile": "RP1" | "RP2" | "RP3" | "RP4" | "RP5",
        "target_volatility": 0.12,  // Optional, derived from risk profile if not provided
        "active_risk_percentage": 0.30,  // Optional Layer 2 active risk split (0.0-1.0)
        "weight_type": "dynamic" | "equilibrium",  // Optional, default: "dynamic"
        "investment_amount": 1000000  // Optional, total amount to invest for dollar allocations
    }

    Response:
    {
        "success": true,
        "timestamp": "2024-01-15T10:30:00Z",
        "layers": {
            "layer1": { ... },  // Asset class weights
            "layer2": { ... },  // Active/passive split and risk budgets
            "layer3": { ... }   // Securities and manager allocations
        },
        "portfolio_summary": {
            "total_volatility": 0.10,
            "expected_return": 0.07,  // Calculated from CMA data
            ...
        },
        "investment_allocations": {  // Only if investment_amount provided
            "total_investment": 1000000,
            "by_asset_class": { ... },
            "by_security": [ ... ]  // With dollar amounts
        }
    }
    """
    try:
        data = request.get_json() or {}

        # Get parameters with defaults
        risk_profile = data.get("risk_profile", "RP3")
        target_volatility = data.get(
            "target_volatility"
        )  # Optional - derived from risk profile
        active_risk_percentage = data.get(
            "active_risk_percentage"
        )  # Optional - Layer 2 risk split override
        weight_type = data.get("weight_type", "dynamic")
        investment_amount = data.get("investment_amount")  # Optional - for dollar allocations

        # Validate risk_profile
        valid_profiles = ["RP1", "RP2", "RP3", "RP4", "RP5"]
        if risk_profile not in valid_profiles:
            return (
                jsonify(
                    {
                        "error": "Invalid risk_profile",
                        "message": f'risk_profile must be one of: {", ".join(valid_profiles)}',
                        "code": "INVALID_RISK_PROFILE",
                    }
                ),
                400,
            )

        # Validate weight_type
        valid_weight_types = ["dynamic", "equilibrium"]
        if weight_type not in valid_weight_types:
            return (
                jsonify(
                    {
                        "error": "Invalid weight_type",
                        "message": f'weight_type must be one of: {", ".join(valid_weight_types)}',
                        "code": "INVALID_WEIGHT_TYPE",
                    }
                ),
                400,
            )

        # Validate target_volatility if provided
        if target_volatility is not None:
            try:
                target_volatility = float(target_volatility)
                if not (0.05 <= target_volatility <= 0.20):
                    return (
                        jsonify(
                            {
                                "error": "Invalid target_volatility",
                                "message": "target_volatility must be between 0.05 and 0.20 (5% to 20%)",
                                "code": "INVALID_TARGET_VOLATILITY",
                            }
                        ),
                        400,
                    )
            except (TypeError, ValueError):
                return (
                    jsonify(
                        {
                            "error": "Invalid target_volatility",
                            "message": "target_volatility must be a number",
                            "code": "INVALID_TARGET_VOLATILITY",
                        }
                    ),
                    400,
                )

        # Validate investment_amount if provided
        if investment_amount is not None:
            try:
                investment_amount = float(investment_amount)
                if investment_amount <= 0:
                    return (
                        jsonify(
                            {
                                "error": "Invalid investment_amount",
                                "message": "investment_amount must be a positive number",
                                "code": "INVALID_INVESTMENT_AMOUNT",
                            }
                        ),
                        400,
                    )
            except (TypeError, ValueError):
                return (
                    jsonify(
                        {
                            "error": "Invalid investment_amount",
                            "message": "investment_amount must be a number",
                            "code": "INVALID_INVESTMENT_AMOUNT",
                        }
                    ),
                    400,
                )

        # Validate active_risk_percentage if provided
        if active_risk_percentage is not None:
            try:
                active_risk_percentage = float(active_risk_percentage)

                # Accept both decimal (0.3) and percent (30) formats.
                if 1.0 < active_risk_percentage <= 100.0:
                    active_risk_percentage = active_risk_percentage / 100.0

                if not (0.0 <= active_risk_percentage <= 1.0):
                    return (
                        jsonify(
                            {
                                "error": "Invalid active_risk_percentage",
                                "message": (
                                    "active_risk_percentage must be between 0 and 1 "
                                    "(or 0 to 100 for percent input)"
                                ),
                                "code": "INVALID_ACTIVE_RISK_PERCENTAGE",
                            }
                        ),
                        400,
                    )
            except (TypeError, ValueError):
                return (
                    jsonify(
                        {
                            "error": "Invalid active_risk_percentage",
                            "message": "active_risk_percentage must be a number",
                            "code": "INVALID_ACTIVE_RISK_PERCENTAGE",
                        }
                    ),
                    400,
                )

        # Run optimization
        result = run_optimization_json(
            risk_profile=risk_profile,
            target_volatility=target_volatility,
            weight_type=weight_type,
            investment_amount=investment_amount,
            active_risk_percentage=active_risk_percentage,
        )

        # Check if optimization was successful
        if not result.get("success", False):
            return jsonify(result), 500

        return jsonify(result), 200

    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Internal server error",
                    "message": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            500,
        )


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=False)
