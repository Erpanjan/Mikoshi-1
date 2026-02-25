# Neo Engine + Gemini AI Integration - Summary

## Overview

Convert Neo Engine's three-layer portfolio optimization to work with Google Gemini function calling in your existing NestJS application.

## Your Requirements

- ✅ **Single function**: One simple function with minimal parameters
- ✅ **Parameters**: Only `risk_profile` and `target_volatility` (dynamic per user)
- ✅ **Backend-managed data**: Excel files managed by marketing team
- ✅ **AI Platform**: Google Gemini (already integrated in NestJS)
- ✅ **Format**: JSON input/output

## Recommended Solution: Hybrid Architecture

```
Gemini AI
   ↓
NestJS Application (your existing app)
   ↓
Python Microservice (FastAPI) - wraps existing Neo Engine code
   ↓
Returns JSON results
```

### Why Hybrid?

1. **Fast**: 1-1.5 weeks vs 4-8 weeks for full JavaScript port
2. **Reliable**: Reuses existing, proven Python optimization code
3. **Maintainable**: Marketing team continues using existing Python code
4. **Low risk**: No complex numerical algorithm rewrites

## The Single Function

```typescript
// Gemini function definition
optimizePortfolio({
  risk_profile: "RP1" | "RP2" | "RP3" | "RP4" | "RP5",
  target_volatility: number  // e.g., 0.12 for 12%
})

// Returns:
{
  success: true,
  portfolio: {...},           // Asset allocations
  layer1_results: {...},      // SAA weights
  layer2_results: {...},      // Active risk allocations
  layer3_results: {...},      // Manager selections
  metrics: {...}              // Risk/return metrics
}
```

## What Needs to Be Built

### 1. Python Microservice (FastAPI)

**New file**: `python-optimizer-service/main.py`

- Wraps existing `run_layered_optimization()` function
- Exposes REST API: `POST /optimize-portfolio`
- Accepts parameters + file paths, returns JSON
- ~300 lines of new code

**Modifications to existing code**:
- [SAA Model/layers/L2/layer2_active_risk.py:570](SAA%20Model/layers/L2/layer2_active_risk.py#L570) - Refactor to return JSON
- [SAA Model/layers/reporting/export.py](SAA%20Model/layers/reporting/export.py) - Add JSON export

### 2. NestJS Integration

**New files**:
- `src/portfolio/portfolio.service.ts` - Calls Python service
- `src/portfolio/portfolio.controller.ts` - REST endpoint (optional)
- `src/ai/gemini-functions.ts` - Function definition for Gemini
- `src/ai/gemini.service.ts` - Update to handle function calls

**Environment variables** (add to .env):
```
PYTHON_SERVICE_URL=http://localhost:8000
DATA_FILE_PATH=/app/data/VLTC_CMA.xlsx
ACTIVE_EXPOSURE_FILE=/app/data/Active_Exposure_Conviction.xlsx
ASSET_ALLOCATION_FILE=/app/data/Passive_Vehicle_Selection.xlsx
MANAGER_SELECTION_FILE=/app/data/Active_Manager_Selection.xlsx
```

### 3. Data Management

- Marketing team uploads Excel files to shared location (e.g., `/app/data/`)
- File paths configured in environment variables
- NestJS reads paths, passes to Python service
- Python service reads Excel files and runs optimization
- Results returned as JSON

## Implementation Timeline

| Phase | Duration |
|-------|----------|
| Python microservice setup | 2-3 days |
| NestJS integration | 2-3 days |
| Gemini function definition | 1-2 days |
| Testing & validation | 2-3 days |
| **Total** | **7-11 days** |

## Example User Flow

**User to Gemini**: "Can you optimize my portfolio for a moderate risk profile with 10% volatility?"

**Gemini extracts**:
- risk_profile: "RP3" (moderate)
- target_volatility: 0.10

**Gemini calls function**: `optimizePortfolio({ risk_profile: "RP3", target_volatility: 0.10 })`

**Flow**:
1. NestJS receives function call
2. Retrieves file paths from config
3. Calls Python service: `POST /optimize-portfolio`
4. Python runs `run_layered_optimization()` with existing code
5. Returns JSON results to NestJS
6. NestJS returns to Gemini
7. Gemini formats response for user

## Key Files to Reference

### Current Neo Engine Files
- [SAA Model/layers/L2/layer2_active_risk.py:570](SAA%20Model/layers/L2/layer2_active_risk.py#L570) - Main orchestration function
- [SAA Model/layers/L1/layer1_saa.py](SAA%20Model/layers/L1/layer1_saa.py) - Layer 1 SAA
- [SAA Model/layers/layer_types.py](SAA%20Model/layers/layer_types.py) - Data structures

### Current System Architecture
- 3 layers: SAA (L1) → Active Risk (L2) → Manager Selection (L3)
- 15 asset classes, 5 risk profiles
- Black-Litterman optimization, mean-variance optimization
- ~2,500 lines of Python code
- Dependencies: NumPy, SciPy, Pandas, OpenPyXL

## Next Steps

1. Review the detailed plan at: `~/.claude/plans/snug-churning-simon.md`
2. Decide on deployment strategy (Docker Compose recommended)
3. Set up Python microservice repository
4. Integrate with your NestJS application
5. Test end-to-end with Gemini

## Questions to Consider

1. Where will Excel data files be stored in production?
2. How often does marketing team update data files?
3. What level of caching do you want for repeated requests?
4. Do you need admin endpoints for data file management?
5. What authentication/authorization for Python service?

## Alternative Approach: Pure JavaScript

**Not recommended** because:
- 4-8 weeks development time
- Complex optimization library integration
- Extensive numerical testing required
- Higher maintenance burden

Only consider if hybrid approach is blocked by infrastructure/security constraints.

---

**Full implementation plan**: `~/.claude/plans/snug-churning-simon.md`

**Contact**: Continue conversation in your preferred editor with this context.
