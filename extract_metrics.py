from __future__ import annotations
from typing import Dict, Any, List
from collections import defaultdict
from simulation import Supplier, ScenarioConfig, Logger


def gini(values: List[float]) -> float:
    """Calculates Gini coefficient of inequality."""
    # Filter out negatives just in case, but keep ZEROS
    vals = [max(0.0, v) for v in values]
    n = len(vals)
    if n == 0 or sum(vals) == 0: return 0.0

    vals.sort()
    cum = 0.0
    for i, v in enumerate(vals, start=1):
        cum += i * v

    # Standard Gini Formula
    return (2.0 * cum) / (n * sum(vals)) - (n + 1.0) / n


def extract_metrics(
        scenario_key: str,
        scenario: ScenarioConfig,
        suppliers: List[Supplier],
        logger: Logger,
        seed: int,
) -> Dict[str, Any]:
    # 1. Aggregate Allocations from Log
    Q_by_id = defaultdict(float)
    for alloc_t in logger.allocations_per_t:
        for (sid, _bid), q in alloc_t.items():
            Q_by_id[sid] += float(q)

    total_alloc = sum(Q_by_id.values())

    # 2. Calculate Shares for ALL Suppliers (Including Zeros)
    # --- THIS WAS THE BUG FIX ---
    shares = []
    for s in suppliers:
        qty = Q_by_id.get(s.id, 0.0)  # Default to 0.0 if not in logs
        share = qty / total_alloc if total_alloc > 0 else 0.0
        shares.append(share)

    share_gini = gini(shares)
    share_max = max(shares) if shares else 0.0

    # 3. Calculate Environmental Impact (Water & Energy)
    total_water = 0.0
    total_energy = 0.0

    # Lookup map for supplier properties
    supp_map = {s.id: s for s in suppliers}

    for sid, q in Q_by_id.items():
        if sid in supp_map:
            s = supp_map[sid]
            total_water += q * s.water_footprint
            total_energy += q * s.energy_footprint

    # Waste is stored in the agent
    total_waste = sum(s.waste_generated for s in suppliers)

    # 3.5. Time Series Data
    # Used for Figure 5 (Winter Collapse)
    supply_series = logger.allocated_total_per_t

    # 4. Group Shares (Indoor vs Outdoor)
    group_shares = {"Indoor": 0.0, "Outdoor": 0.0}
    for sid, q in Q_by_id.items():
        if "Indoor" in sid:
            group_shares["Indoor"] += q
        elif "Outdoor" in sid:
            group_shares["Outdoor"] += q

    # Normalize shares
    if total_alloc > 0:
        for k in group_shares:
            group_shares[k] /= total_alloc

    # 5. Costs
    if logger.cost_total_per_t:
        cost_total_sum = sum(logger.cost_total_per_t)
        cost_mean = cost_total_sum / len(logger.cost_total_per_t)
    else:
        cost_mean = 0.0

    # Calculate Participation Rate (active / total)
    n_active = sum(1 for s in shares if s > 1e-9)
    participation_rate = n_active / len(suppliers) if suppliers else 0.0

    return {
        "scenario_key": scenario_key,
        "scenario_name": scenario.name,
        "summary": {
            "total_allocated": total_alloc,
            "share_gini": share_gini,
            "share_max": share_max,
            "total_water": total_water,
            "total_energy": total_energy,
            "total_waste": total_waste,
            "cost_mean": cost_mean,
            "participation_rate": participation_rate
        },
        "groups": group_shares,
        # --- NEW: Added this block for the Time Series Plot ---
        "timeseries": {
            "supply": supply_series
        }
    }