from __future__ import annotations
from typing import Dict, Any, List
import statistics

from simulation import Supplier, ScenarioConfig, Logger


def infer_group(supplier_id: str) -> str:
    return supplier_id[0].upper() if supplier_id else "?"


def gini(values: List[float]) -> float:
    vals = [max(0.0, float(v)) for v in values]
    s = sum(vals)
    n = len(vals)
    if n == 0 or s == 0:
        return 0.0
    vals.sort()
    cum = 0.0
    for i, v in enumerate(vals, start=1):
        cum += i * v
    return (2.0 * cum) / (n * s) - (n + 1.0) / n


def extract_metrics(
    scenario_key: str,
    scenario: ScenarioConfig,
    suppliers: List[Supplier],
    logger: Logger,
    seed: int = 42,
) -> Dict[str, Any]:
    T = scenario.T

    # --- timeseries from logger ---
    co2_prod = [e["CO2_prod"] for e in logger.emissions_per_t[:T]]
    co2_trans = [e["CO2_trans"] for e in logger.emissions_per_t[:T]]
    co2_total = [e["CO2_total"] for e in logger.emissions_per_t[:T]]
    cost_total = list(logger.cost_total_per_t[:T])
    allocated_total = list(logger.allocated_total_per_t[:T])

    # --- summary ---
    co2_prod_sum = sum(co2_prod)
    co2_trans_sum = sum(co2_trans)
    co2_total_sum = sum(co2_total)
    cost_total_sum = sum(cost_total)

    co2_total_mean = co2_total_sum / len(co2_total) if co2_total else 0.0
    cost_total_mean = cost_total_sum / len(cost_total) if cost_total else 0.0

    total_allocated = sum(allocated_total)

    # --- supplier stats ---
    total_Q = sum(s.Q for s in suppliers)
    total_Cap = sum(s.cap_nominal for s in suppliers)

    by_id: Dict[str, Dict[str, float]] = {}
    shares: List[float] = []

    for s in suppliers:
        Q = float(s.Q)
        H = Q / total_Q if total_Q > 0 else 0.0
        E = float(s.cap_nominal) / total_Cap if total_Cap > 0 else 0.0
        shares.append(H)
        by_id[s.id] = {
            "Q": Q,
            "H": H,
            "E": E,
            "F_rot": float(s.F_rot),
            "F_disp": float(s.F_disp),
            "F_uni": float(s.F_unified),
        }

    by_group: Dict[str, Dict[str, float]] = {}
    for sid, rec in by_id.items():
        g = infer_group(sid)
        by_group.setdefault(g, {"Q": 0.0, "H": 0.0})
        by_group[g]["Q"] += rec["Q"]
        by_group[g]["H"] += rec["H"]

    share_gini = gini(shares)
    share_max = max(shares) if shares else 0.0
    share_std = statistics.pstdev(shares) if len(shares) > 1 else 0.0

    metrics: Dict[str, Any] = {
        "meta": {
            "scenario_key": scenario_key,
            "scenario_name": scenario.name,
            "T": scenario.T,
            "tau": scenario.tau,
            "w_c": scenario.w_c,
            "w_e": scenario.w_e,
            "w_f": scenario.w_f,
            "alpha": scenario.alpha,
            "beta": scenario.beta,
            "gamma": scenario.gamma,
            "delta": scenario.delta,
            "use_individualized_lca": scenario.use_individualized_lca,
            "use_fairness": scenario.use_fairness,
            "allocation_mode": scenario.allocation_mode,
            "seed": seed,
        },
        "timeseries": {
            "co2_prod": co2_prod,
            "co2_trans": co2_trans,
            "co2_total": co2_total,
            "cost_total": cost_total,
            "allocated_total": allocated_total,
        },
        "summary": {
            "co2_prod_sum": co2_prod_sum,
            "co2_trans_sum": co2_trans_sum,
            "co2_total_sum": co2_total_sum,
            "co2_total_mean": co2_total_mean,
            "cost_total_sum": cost_total_sum,
            "cost_total_mean": cost_total_mean,
            "total_allocated": total_allocated,
            "share_gini": share_gini,
            "share_max": share_max,
            "share_std": share_std,
        },
        "suppliers": {
            "by_id": by_id,
            "by_group": by_group,
        },
    }
    return metrics
