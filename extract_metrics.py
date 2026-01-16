from __future__ import annotations

from typing import Dict, Any, List, Tuple
from collections import defaultdict

from simulation import Supplier, ScenarioConfig, Logger


def gini(values: List[float]) -> float:
    """Gini coefficient for nonnegative values."""
    vals = [v for v in values if v >= 0]
    n = len(vals)
    if n == 0:
        return 0.0
    s = sum(vals)
    if s == 0:
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
    seed: int,
) -> Dict[str, Any]:
    """
    Compute summary metrics for a completed simulation run.
    Works for ALL scenarios (fairness on/off, sequential/proportional).
    """

    # -----------------------------
    # 1) Aggregate allocations Q_s from logger
    # -----------------------------
    Q_by_supplier = defaultdict(float)

    for alloc_t in logger.allocations_per_t:
        for (sid, _bid), q in alloc_t.items():
            Q_by_supplier[sid] += float(q)

    total_alloc = sum(Q_by_supplier.values())

    # If logging is missing, fall back to Supplier.Q (still works if update_fairness ran)
    if total_alloc == 0.0:
        Q_by_supplier = {s.id: float(s.Q) for s in suppliers}
        total_alloc = sum(Q_by_supplier.values())

    n_suppliers = len(suppliers)
    eps = 1e-12  # avoids counting tiny floating allocations
    n_active = sum(1 for sid in [s.id for s in suppliers] if float(Q_by_supplier.get(sid, 0.0)) > eps)
    participation_rate = (n_active / n_suppliers) if n_suppliers else 0.0

    # Historical shares H_s
    if total_alloc > 0:
        H_by_supplier = {sid: q / total_alloc for sid, q in Q_by_supplier.items()}
    else:
        H_by_supplier = {s.id: 0.0 for s in suppliers}

    share_vals = [H_by_supplier.get(s.id, 0.0) for s in suppliers]
    share_gini = gini(share_vals)
    share_max = max(share_vals) if share_vals else 0.0

    # -----------------------------
    # 2) Group shares (A/B/C) from supplier IDs
    # -----------------------------
    group = {"A": 0.0, "B": 0.0, "C": 0.0}
    for sid, h in H_by_supplier.items():
        if sid.startswith("A"):
            group["A"] += h
        elif sid.startswith("B"):
            group["B"] += h
        elif sid.startswith("C"):
            group["C"] += h

    # -----------------------------
    # 3) Emissions aggregates
    # -----------------------------
    co2_prod_sum = sum(e.get("CO2_prod", 0.0) for e in logger.emissions_per_t)
    co2_trans_sum = sum(e.get("CO2_trans", 0.0) for e in logger.emissions_per_t)
    co2_total_sum = sum(e.get("CO2_total", 0.0) for e in logger.emissions_per_t)

    T = len(logger.emissions_per_t) if logger.emissions_per_t else max(1, scenario.T)
    co2_total_mean = co2_total_sum / T

    # -----------------------------
    # 4) Cost aggregates (if you logged cost in metrics; if not, keep placeholder)
    # -----------------------------
    # If your extract code already computes cost_total_per_t in results.json, keep using it.
    # Otherwise you can compute per timestep from allocations:
    # cost_total_t = sum(q * (c_s + tau*co2_s) ) or whatever your definition is.
    # For now, assume you stored it in results.json elsewhere, or compute here if you want.

    # Placeholder: if you have cost logged per timestep in emissions dict, read it; else 0.
    #cost_total_sum = sum(logger.cost_total_per_t) if hasattr(logger, "cost_total_per_t") else 0.0
    #cost_total_mean = cost_total_sum / T if T > 0 else 0.0

    if hasattr(logger, "cost_total_per_t") and logger.cost_total_per_t:
        cost_total_sum = sum(logger.cost_total_per_t)
        cost_total_mean = cost_total_sum / len(logger.cost_total_per_t)
    else:
        cost_total_sum = 0.0
        cost_total_mean = 0.0

    # -----------------------------
    # 5) Package results
    # -----------------------------
    # -----------------------------
    # 5) Package results (MATCH plot_results.py schema)
    # -----------------------------
    return {
        "scenario_key": scenario_key,
        "scenario_name": scenario.name,
        "seed": seed,
        "T": scenario.T,
        "params": {
            "tau": scenario.tau,
            "w_c": scenario.w_c, "w_e": scenario.w_e, "w_f": scenario.w_f,
            "alpha": scenario.alpha, "beta": scenario.beta, "gamma": scenario.gamma,
            "delta": scenario.delta,
            "use_individualized_lca": scenario.use_individualized_lca,
            "use_fairness": scenario.use_fairness,
            "allocation_mode": scenario.allocation_mode,
        },
        "summary": {
            "total_allocated": total_alloc,
            "share_gini": share_gini,
            "share_max": share_max,
            "co2_prod_sum": co2_prod_sum,
            "co2_trans_sum": co2_trans_sum,
            "co2_total_sum": co2_total_sum,
            "co2_total_mean": co2_total_mean,
            "cost_total_sum": cost_total_sum,
            "cost_total_mean": cost_total_mean,
            "participation_rate": participation_rate,
            "n_active_suppliers": n_active,
            "n_suppliers": n_suppliers,
        },
        "suppliers": {
            "by_group": {
                "A": {"H": group["A"]},
                "B": {"H": group["B"]},
                "C": {"H": group["C"]},
            },
            # optional: keep supplier-level too, for later plots
            "by_id": {
                sid: {"Q": float(Q_by_supplier[sid]), "H": float(H_by_supplier.get(sid, 0.0))}
                for sid in Q_by_supplier.keys()
            },
        },
    }

