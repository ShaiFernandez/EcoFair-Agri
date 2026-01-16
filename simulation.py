from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import random


# =========================
#  AGENT DATA STRUCTURES
# =========================

@dataclass
class Supplier:
    # 1. Required Fields (No Defaults)
    id: str
    c: float  # Unit Price (P_i)
    water_footprint: float  # Liters per unit (W)
    energy_footprint: float  # kWh per unit (E)
    cap_nominal: float  # Nominal capacity Cap_s
    distances: Dict[str, float]  # Distance to buyer

    # 2. Fields with Defaults (Must come AFTER required fields)
    reputation: float = 1.0  # Historical Reputation (Rep_i)

    # Fairness state
    Q: float = 0.0  # cumulative allocated quantity Q_s
    F_rot: float = 0.0  # rotation fairness
    F_disp: float = 1.0  # disparity fairness
    F_unified: float = 1.0  # unified fairness signal
    rot_wait: int = 0
    cap_available: float = 0.0

    def reset_capacity(self):
        self.cap_available = self.cap_nominal


@dataclass
class Buyer:
    id: str
    demand_nominal: float
    w_c: float = 1.0
    w_e: float = 0.0
    w_f: float = 0.0
    demand_remaining: float = 0.0

    def reset_demand(self):
        self.demand_remaining = self.demand_nominal


# =========================
#  SCENARIO CONFIGURATION
# =========================

@dataclass
class ScenarioConfig:
    name: str
    T: int

    # --- NEW: SCARCITY & TAX PARAMS ---
    scarcity_cost_water: float  # $/Liter
    scarcity_cost_energy: float  # $/kWh
    # -----------------------------

    # Ranking Weights (Equation 2)
    alpha: float  # Weight for Cost (Price + Tax)
    beta: float  # Weight for Reputation
    gamma: float  # Weight for Fairness

    use_individualized_lca: bool
    use_fairness: bool
    allocation_mode: str
    delta: float = 0.5

    # --- LEGACY FIELDS (Defaults to 0.0 to prevent errors) ---
    tau: float = 0.0
    w_c: float = 0.0
    w_e: float = 0.0
    w_f: float = 0.0


# =========================
#  ENVIRONMENTAL DATA MODULE
# =========================

class EnvironmentalDataModule:
    def __init__(self, static_co2: float, individualized_co2: Dict[str, float], co2_per_km: float):
        self.static_co2 = static_co2
        self.individualized_co2 = individualized_co2
        self.co2_per_km = co2_per_km

    def get_distance(self, supplier: Supplier, buyer: Buyer) -> float:
        return supplier.distances.get(buyer.id, 0.0)

    # Legacy method wrapper
    def get_co2(self, supplier, scenario):
        return 0.0

    # =========================


#  FAIRNESS MODULE
# =========================

class FairnessModule:
    def __init__(self, delta: float, eps: float = 1e-9, disp_cap: float = 5.0):
        self.delta = delta
        self.eps = eps
        self.disp_cap = disp_cap

    def update_fairness(self, suppliers: List[Supplier], allocations: Dict[Tuple[str, str], float]) -> None:
        allocated_by_supplier = {s.id: 0.0 for s in suppliers}
        for (sid, _), q in allocations.items():
            allocated_by_supplier[sid] += q

        for s in suppliers:
            s.Q += allocated_by_supplier[s.id]

        # Rotation
        for s in suppliers:
            if allocated_by_supplier[s.id] > 0:
                s.rot_wait = 0
            else:
                s.rot_wait += 1
            s.F_rot = 1.0 / (1.0 + s.rot_wait)

        # Disparity
        total_Q = sum(s.Q for s in suppliers)
        total_Cap = sum(s.cap_nominal for s in suppliers)

        if total_Q <= self.eps or total_Cap <= self.eps:
            for s in suppliers: s.F_disp = 1.0
        else:
            for s in suppliers:
                H_s = s.Q / (total_Q + self.eps)
                E_s = s.cap_nominal / (total_Cap + self.eps)
                ratio = H_s / (E_s + self.eps)
                ratio = max(self.eps, min(self.disp_cap, ratio))
                s.F_disp = ratio

        for s in suppliers:
            s.F_unified = self.delta * s.F_rot + (1.0 - self.delta) * s.F_disp


# =========================
#  POLICY & SCORING MODULE
# =========================

class PolicyScoringModule:
    def __init__(self, scenario: ScenarioConfig):
        self.scenario = scenario

    def calculate_environmental_tax(self, s: Supplier) -> float:
        # Equation 1: Tax = (W * Cost_W) + (E * Cost_E)
        tax_water = s.water_footprint * self.scenario.scarcity_cost_water
        tax_energy = s.energy_footprint * self.scenario.scarcity_cost_energy
        return tax_water + tax_energy

    def compute_scores(self, suppliers: List[Supplier], buyer: Buyer) -> Dict[str, float]:
        scores = {}

        total_costs = []
        for s in suppliers:
            tax = self.calculate_environmental_tax(s)
            total_costs.append(s.c + tax)

        max_cost = max(total_costs) if total_costs else 1.0

        for s, total_c in zip(suppliers, total_costs):
            # 1. Cost Score (Higher is better)
            norm_cost = 1.0 - (total_c / (max_cost * 1.2))
            if norm_cost < 0: norm_cost = 0

            # 2. Fairness
            norm_fairness = s.F_unified

            # 3. Reputation
            norm_reputation = s.reputation

            # Equation 2: Weighted Sum
            S_i = (self.scenario.alpha * norm_cost) + \
                  (self.scenario.beta * norm_reputation) + \
                  (self.scenario.gamma * norm_fairness)

            scores[s.id] = S_i

        return scores

    def carbon_adjusted_cost(self, base_cost, co2):
        return base_cost

    # =========================


#  MARKETPLACE MODULE
# =========================

class MarketplaceModule:
    def __init__(self, env_module, fairness_module, policy_module):
        self.env = env_module
        self.fairness = fairness_module
        self.policy = policy_module

    def refresh_state(self, suppliers, buyers):
        for s in suppliers: s.reset_capacity()
        for b in buyers: b.reset_demand()

    def filter_suppliers(self, suppliers):
        return [s for s in suppliers if s.cap_available > 0]

    def rank_suppliers(self, suppliers, buyer):
        scores = self.policy.compute_scores(suppliers, buyer)
        ranked = sorted(suppliers, key=lambda s: scores.get(s.id, 0.0), reverse=True)
        return ranked

    def allocate_sequential(self, ranked_suppliers, buyer):
        allocations = {}
        for s in ranked_suppliers:
            if buyer.demand_remaining <= 0: break
            if s.cap_available <= 0: continue
            q = min(buyer.demand_remaining, s.cap_available)
            allocations[(s.id, buyer.id)] = q
            s.cap_available -= q
            buyer.demand_remaining -= q
        return allocations

    def allocate_proportional(self, eligible_suppliers, buyer):
        allocations = {}
        scores = self.policy.compute_scores(eligible_suppliers, buyer)
        total_score = sum(scores.values())
        if total_score == 0: return allocations

        for s in eligible_suppliers:
            share = scores[s.id] / total_score
            q = share * buyer.demand_remaining
            q = min(q, s.cap_available)
            allocations[(s.id, buyer.id)] = q
            s.cap_available -= q
        buyer.demand_remaining = 0
        return allocations

    def compute_emissions(self, suppliers, buyer, allocations):
        return {"CO2_prod": 0.0, "CO2_trans": 0.0, "CO2_total": 0.0}

    def compute_cost_total(self, suppliers, allocations):
        total = 0.0
        s_map = {s.id: s for s in suppliers}
        for (sid, _), q in allocations.items():
            s = s_map[sid]
            total += q * s.c
        return total


# =========================
#  LOGGER
# =========================

class Logger:
    def __init__(self):
        self.allocations_per_t = []
        self.emissions_per_t = []
        self.cost_total_per_t = []
        self.allocated_total_per_t = []
        self.fairness_snapshots = []

    def record(self, t, allocations, suppliers, emissions, cost_total):
        self.allocations_per_t.append(dict(allocations))
        self.emissions_per_t.append(dict(emissions))
        self.cost_total_per_t.append(float(cost_total))
        self.allocated_total_per_t.append(sum(float(q) for q in allocations.values()))
        self.fairness_snapshots.append({
            s.id: {"Q": s.Q, "F_unified": s.F_unified} for s in suppliers
        })


# =========================
#  SIMULATION CORE
# =========================

class Simulation:
    def __init__(self, suppliers, buyers, env_module, fairness_module, policy_module, marketplace, logger, scenario):
        self.suppliers = suppliers
        self.buyers = buyers
        self.env = env_module
        self.fairness = fairness_module
        self.policy = policy_module
        self.marketplace = marketplace
        self.logger = logger
        self.scenario = scenario

    def run(self):
        T = self.scenario.T
        buyer = self.buyers[0]
        for t in range(1, T + 1):
            self.marketplace.refresh_state(self.suppliers, self.buyers)
            eligible = self.marketplace.filter_suppliers(self.suppliers)

            if self.scenario.allocation_mode == "sequential":
                ranked = self.marketplace.rank_suppliers(eligible, buyer)
                allocations = self.marketplace.allocate_sequential(ranked, buyer)
            else:
                allocations = self.marketplace.allocate_proportional(eligible, buyer)

            if self.scenario.use_fairness:
                self.fairness.update_fairness(self.suppliers, allocations)

            emissions = self.marketplace.compute_emissions(self.suppliers, buyer, allocations)
            cost = self.marketplace.compute_cost_total(self.suppliers, allocations)
            self.logger.record(t, allocations, self.suppliers, emissions, cost)


# =========================
#  FARMER GENERATION
# =========================

def create_farmers_AB() -> List[Supplier]:
    suppliers: List[Supplier] = []
    buyer_ids = ["B1"]

    # Type A: Indoor (High Cost, Low Water, High Energy)
    for i in range(3):
        suppliers.append(Supplier(
            id=f"Indoor_{i + 1}",
            c=2.50,
            water_footprint=10.0,
            energy_footprint=5.0,
            cap_nominal=100.0,
            distances={b: 10.0 for b in buyer_ids}
        ))

    # Type B: Outdoor (Low Cost, High Water, Low Energy)
    for i in range(3):
        suppliers.append(Supplier(
            id=f"Outdoor_{i + 1}",
            c=1.50,
            water_footprint=100.0,
            energy_footprint=1.0,
            cap_nominal=100.0,
            distances={b: 200.0 for b in buyer_ids},
            reputation=0.85  # Lower reliability
        ))

    return suppliers


def create_example_buyer() -> Buyer:
    return Buyer(id="B1", demand_nominal=120.0)