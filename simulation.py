from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import random


# =========================
#  AGENT DATA STRUCTURES
#  (Section III-B, IV-B)
# =========================

@dataclass
class Supplier:
    id: str
    c: float                      # base cost c_s
    co2: float                    # production CO2 intensity CO2_s
    cap_nominal: float            # nominal capacity Cap_s
    distances: Dict[str, float]   # d_{sb} for each buyer id

    # Fairness state (Section III-C)
    Q: float = 0.0                # cumulative allocated quantity Q_s
    F_rot: float = 0.0            # rotation fairness F^{rot}_s
    F_disp: float = 1.0           # disparity fairness F^{disp}_s
    F_unified: float = 1.0        # unified fairness signal F_s

    rot_wait: int = 0 # rounds since last selected (r_s)

    # Runtime capacity per timestep
    cap_available: float = 0.0    # refreshed each timestep

    def reset_capacity(self):
        self.cap_available = self.cap_nominal


@dataclass
class Buyer:
    id: str
    demand_nominal: float         # D_b per timestep
    w_c: float                    # weight for cost
    w_e: float                    # weight for CO2
    w_f: float                    # weight for fairness

    # Runtime demand per timestep
    demand_remaining: float = 0.0

    def reset_demand(self):
        self.demand_remaining = self.demand_nominal


# =========================
#  SCENARIO CONFIGURATION
#  (Section III-F, IV-D)
# =========================

@dataclass
class ScenarioConfig:
    name: str
    T: int                        # number of timesteps
    tau: float                    # carbon price τ
    w_c: float                    # ranking weights (could override buyer’s)
    w_e: float
    w_f: float
    alpha: float                  # allocation weights for cost
    beta: float                   # allocation weights for CO2
    gamma: float                  # allocation weights for fairness
    use_individualized_lca: bool  # True = individualized, False = static
    use_fairness: bool            # whether fairness is active
    allocation_mode: str          # "sequential" or "proportional"
    delta: float = 0.5            # fairness combination parameter


# =========================
#  ENVIRONMENTAL DATA MODULE
#  (Section III-D, IV-A.2)
# =========================

class EnvironmentalDataModule:
    def __init__(self,
                 static_co2: float,
                 individualized_co2: Dict[str, float],
                 co2_per_km: float):
        """
        static_co2: industry-average CO2 intensity
        individualized_co2: mapping supplier_id -> CO2_s
        co2_per_km: CO2_km factor
        """
        self.static_co2 = static_co2
        self.individualized_co2 = individualized_co2
        self.co2_per_km = co2_per_km

    def get_co2(self, supplier: Supplier, scenario: ScenarioConfig) -> float:
        """Return CO2_s depending on dataset used (static vs individualized)."""
        if scenario.use_individualized_lca:
            return self.individualized_co2.get(supplier.id, self.static_co2)
        else:
            return self.static_co2

    def get_distance(self, supplier: Supplier, buyer: Buyer) -> float:
        """Return distance d_{sb} (assumed already set in supplier.distances)."""
        return supplier.distances[buyer.id]


# =========================
#  FAIRNESS MODULE
#  (Section III-C, III-G, IV-A.3)
# =========================

class FairnessModule:
    def __init__(self, delta: float, eps: float = 1e-9, disp_cap: float = 5.0):
        """
        delta: mix between rotation and disparity (0..1)
        eps: numerical stability
        disp_cap: cap disparity ratio to avoid extreme domination early on
        """
        self.delta = delta
        self.eps = eps
        self.disp_cap = disp_cap

    def update_fairness(
            self,
            suppliers: List[Supplier],
            allocations: Dict[Tuple[str, str], float]
    ) -> None:
        # 1) Update cumulative allocations Q_s
        allocated_by_supplier = {s.id: 0.0 for s in suppliers}
        for (sid, _), q in allocations.items():
            allocated_by_supplier[sid] += q

        for s in suppliers:
            s.Q += allocated_by_supplier[s.id]

        # 2) Rotation fairness update
        for s in suppliers:
            if allocated_by_supplier[s.id] > 0:
                s.rot_wait = 0
            else:
                s.rot_wait += 1

            # lower is better (not selected recently -> smaller value)
            s.F_rot = 1.0 / (1.0 + s.rot_wait)

        # 3) Disparity fairness update (H_s / E_s)
        total_Q = sum(s.Q for s in suppliers)
        total_Cap = sum(s.cap_nominal for s in suppliers)

        # If no history yet, start neutral
        if total_Q <= self.eps or total_Cap <= self.eps:
            for s in suppliers:
                s.F_disp = 1.0
        else:
            for s in suppliers:
                H_s = s.Q / (total_Q + self.eps)
                E_s = s.cap_nominal / (total_Cap + self.eps)

                ratio = H_s / (E_s + self.eps)

                # cap to avoid extreme values dominating the score
                ratio = max(self.eps, min(self.disp_cap, ratio))

                s.F_disp = ratio

        # 4) Unified fairness signal
        for s in suppliers:
            s.F_unified = self.delta * s.F_rot + (1.0 - self.delta) * s.F_disp
            #s.F_unified = s.F_rot  # temporary until disparity is implemented


# =========================
#  POLICY & SCORING MODULE
#  (Section III-C, III-D, III-F, IV-A.4)
# =========================
class PolicyScoringModule:
    def __init__(self, scenario: ScenarioConfig):
        self.scenario = scenario

    def carbon_adjusted_cost(self, base_cost: float, co2: float) -> float:
        """c'_s = c_s + τ * CO2_s"""
        return base_cost + self.scenario.tau * co2

    @staticmethod
    def _minmax(vals, eps=1e-9):
        vmin, vmax = min(vals), max(vals)
        denom = (vmax - vmin) + eps
        return [(v - vmin) / denom for v in vals]

    def compute_scores(self, suppliers, buyer):
        w_c, w_e, w_f = self.scenario.w_c, self.scenario.w_e, self.scenario.w_f

        c_primes = [self.carbon_adjusted_cost(s.c, s.co2) for s in suppliers]
        co2s = [s.co2 for s in suppliers]

        if self.scenario.use_fairness:
            fs = [s.F_unified for s in suppliers]
            fN = self._minmax(fs)
        else:
            fN = [0.0 for _ in suppliers]

        cN = self._minmax(c_primes)
        eN = self._minmax(co2s)

        scores = {}
        for s, cn, en, fn in zip(suppliers, cN, eN, fN):
            scores[s.id] = w_c * cn + w_e * en + w_f * fn

        return scores


"""
class PolicyScoringModule:
    def __init__(self, scenario: ScenarioConfig):
        self.scenario = scenario

    def carbon_adjusted_cost(self, base_cost: float, co2: float) -> float:
        #c'_s = c_s + τ * CO2_s
        return base_cost + self.scenario.tau * co2


    def compute_scores(
        self,
        suppliers: List[Supplier],
        buyer: Buyer,
    ) -> Dict[str, float]:
        ""
        Compute Score_s = w_c c'_s + w_e CO2_s + w_f F_s
        Returns mapping supplier_id -> score.
        ""
        scores = {}
        # Use scenario-level weights or buyer-level? Choose one policy:
        #w_c = buyer.w_c
        #w_e = buyer.w_e
        #w_f = buyer.w_f
        w_c = self.scenario.w_c
        w_e = self.scenario.w_e
        w_f = self.scenario.w_f

        for s in suppliers:
            # co2 is assumed already set on supplier before scoring
            c_prime = self.carbon_adjusted_cost(s.c, s.co2)
            score = w_c * c_prime + w_e * s.co2 + w_f * s.F_unified
            scores[s.id] = score
        return scores
"""

# =========================
#  MARKETPLACE MODULE
#  (Section III-E, III-G, IV-A.5, IV-C)
# =========================

class MarketplaceModule:
    def __init__(self,
                 env_module: EnvironmentalDataModule,
                 fairness_module: FairnessModule,
                 policy_module: PolicyScoringModule):
        self.env = env_module
        self.fairness = fairness_module
        self.policy = policy_module

    def refresh_state(self, suppliers: List[Supplier], buyers: List[Buyer]):
        """Reset capacities and demands at the start of each timestep."""
        for s in suppliers:
            s.reset_capacity()
        for b in buyers:
            b.reset_demand()

    def filter_suppliers(
        self,
        suppliers: List[Supplier],
    ) -> List[Supplier]:
        """Apply basic feasibility: capacity > 0, plus any scenario-specific rules."""
        eligible = [s for s in suppliers if s.cap_available > 0]
        # TODO: apply scenario-specific exclusions if needed
        return eligible

    def rank_suppliers(
        self,
        suppliers: List[Supplier],
        buyer: Buyer
    ) -> List[Supplier]:
        """Compute scores and return suppliers sorted by ascending score."""
        scores = self.policy.compute_scores(suppliers, buyer)
        ranked = sorted(suppliers, key=lambda s: scores[s.id])
        return ranked

    def allocate_sequential(
        self,
        ranked_suppliers: List[Supplier],
        buyer: Buyer
    ) -> Dict[Tuple[str, str], float]:
        """
        Sequential allocation:
        q_{sb,t} = min(D_b, Cap_s)
        """
        allocations: Dict[Tuple[str, str], float] = {}
        for s in ranked_suppliers:
            if buyer.demand_remaining <= 0:
                break
            if s.cap_available <= 0:
                continue

            q = min(buyer.demand_remaining, s.cap_available)
            allocations[(s.id, buyer.id)] = q
            s.cap_available -= q
            buyer.demand_remaining -= q

        return allocations

    def allocate_proportional(
        self,
        eligible_suppliers: List[Supplier],
        buyer: Buyer
    ) -> Dict[Tuple[str, str], float]:
        """
        Proportional allocation based on score-derived weights.
        Example: weight_s = 1 / Score_s.
        """
        allocations: Dict[Tuple[str, str], float] = {}

        scores = self.policy.compute_scores(eligible_suppliers, buyer)
        # TODO: may want to protect against zero or negative scores
        weights = {}
        for s in eligible_suppliers:
            # simple inverse-score weight (you can refine this)
            w = 1.0 / scores[s.id] if scores[s.id] > 0 else 0.0
            weights[s.id] = w

        total_w = sum(weights.values())
        if total_w == 0:
            return allocations  # no meaningful proportional allocation

        for s in eligible_suppliers:
            share = weights[s.id] / total_w
            q = share * buyer.demand_remaining
            q = min(q, s.cap_available)
            allocations[(s.id, buyer.id)] = q
            s.cap_available -= q

        buyer.demand_remaining = 0.0
        return allocations

    def compute_emissions(
        self,
        suppliers: List[Supplier],
        buyer: Buyer,
        allocations: Dict[Tuple[str, str], float]
    ) -> Dict[str, float]:
        """
        Compute CO2^{prod}_t, CO2^{trans}_t, CO2_total,t.
        """
        co2_prod = 0.0
        co2_trans = 0.0

        for (sid, bid), q in allocations.items():
            s = next(sp for sp in suppliers if sp.id == sid)
            co2_prod += q * s.co2

            d_sb = self.env.get_distance(s, buyer)
            co2_trans += d_sb * self.env.co2_per_km * q

        co2_total = co2_prod + co2_trans
        return {
            "CO2_prod": co2_prod,
            "CO2_trans": co2_trans,
            "CO2_total": co2_total,
        }
    def compute_cost_total(
        self,
        suppliers: List[Supplier],
        allocations: Dict[Tuple[str, str], float],
    ) -> float:
        """
        Total procurement cost for the timestep:
        sum_{(s,b)} q_{sb,t} * (c_s + tau*CO2_s)
        """
        total = 0.0
        supplier_map = {s.id: s for s in suppliers}
        for (sid, _), q in allocations.items():
            s = supplier_map[sid]
            c_prime = self.policy.carbon_adjusted_cost(s.c, s.co2)
            total += float(q) * c_prime
        return total



# =========================
#  LOGGER
#  (Section IV-A.5, IV-E)
# =========================

"""
class Logger:
    def __init__(self):
        # store time series
        self.allocations_per_t: List[Dict[Tuple[str, str], float]] = []
        self.emissions_per_t: List[Dict[str, float]] = []
        self.fairness_snapshots: List[Dict[str, Dict[str, float]]] = []

    def record(
        self,
        t: int,
        allocations: Dict[Tuple[str, str], float],
        suppliers: List[Supplier],
        emissions: Dict[str, float],
    ):
        self.allocations_per_t.append(allocations)
        self.emissions_per_t.append(emissions)
        self.fairness_snapshots.append({
            s.id: {
                "Q": s.Q,
                "F_rot": s.F_rot,
                "F_disp": s.F_disp,
                "F_unified": s.F_unified,
            }
            for s in suppliers
        })
"""
class Logger:
    def __init__(self):
        self.allocations_per_t: List[Dict[Tuple[str, str], float]] = []
        self.emissions_per_t: List[Dict[str, float]] = []
        self.cost_total_per_t: List[float] = []
        self.allocated_total_per_t: List[float] = []
        self.fairness_snapshots: List[Dict[str, Dict[str, float]]] = []

    def record(
        self,
        t: int,
        allocations: Dict[Tuple[str, str], float],
        suppliers: List[Supplier],
        emissions: Dict[str, float],
        cost_total: float,
    ):
        self.allocations_per_t.append(dict(allocations))
        self.emissions_per_t.append(dict(emissions))
        self.cost_total_per_t.append(float(cost_total))
        self.allocated_total_per_t.append(sum(float(q) for q in allocations.values()))

        self.fairness_snapshots.append({
            s.id: {
                "Q": s.Q,
                "F_rot": s.F_rot,
                "F_disp": s.F_disp,
                "F_unified": s.F_unified,
            }
            for s in suppliers
        })


# =========================
#  SIMULATION CORE
#  (Section III-G, IV-C)
# =========================

class Simulation:
    def __init__(
        self,
        suppliers: List[Supplier],
        buyers: List[Buyer],
        env_module: EnvironmentalDataModule,
        fairness_module: FairnessModule,
        policy_module: PolicyScoringModule,
        marketplace: MarketplaceModule,
        logger: Logger,
        scenario: ScenarioConfig,
    ):
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
        buyer = self.buyers[0]  # single representative buyer

        for t in range(1, T + 1):
            # 1) Refresh capacities and demand
            self.marketplace.refresh_state(self.suppliers, self.buyers)

            # 2) Update supplier CO2 values (static or individualized)
            for s in self.suppliers:
                s.co2 = self.env.get_co2(s, self.scenario)

            # 3) Filtering
            eligible = self.marketplace.filter_suppliers(self.suppliers)

            # 4) Allocation
            if self.scenario.allocation_mode == "sequential":
                ranked = self.marketplace.rank_suppliers(eligible, buyer)
                allocations = self.marketplace.allocate_sequential(ranked, buyer)
            else:
                allocations = self.marketplace.allocate_proportional(eligible, buyer)

            # 5) Fairness update (only if enabled)
            if self.scenario.use_fairness:
                self.fairness.update_fairness(self.suppliers, allocations)
            else:
                # keep fairness neutral so scoring behaves like "no fairness"
                for s in self.suppliers:
                    s.F_rot = 1.0
                    s.F_disp = 1.0
                    s.F_unified = 1.0

            # 6) Emission calculation
            emissions = self.marketplace.compute_emissions(self.suppliers, buyer, allocations)

            # 6b) Cost calculation
            cost_total = self.marketplace.compute_cost_total(self.suppliers, allocations)

            # 7) Logging
            self.logger.record(t, allocations, self.suppliers, emissions, cost_total)


# =========================
#  EXAMPLE SETUP (stub)
# =========================
"""
def create_example_suppliers() -> List[Supplier]:
    # Do not have actual A/B/C types and distances
    suppliers = []
    buyer_ids = ["B1"]
    for i in range(9):
        s_id = f"S{i+1}"
        # placeholder distance: same for all buyers
        distances = {b: random.uniform(50, 300) for b in buyer_ids}
        suppliers.append(
            Supplier(
                id=s_id,
                c=10.0,
                co2=5.0,
                cap_nominal=100.0,
                distances=distances,
            )
        )
    return suppliers
"""

def create_suppliers_ABC() -> List[Supplier]:
    suppliers: List[Supplier] = []
    buyer_ids = ["B1"]

    # Type A: high cost, low CO2
    for i in range(3):
        s_id = f"A{i+1}"
        distances = {b: random.uniform(50, 300) for b in buyer_ids}
        suppliers.append(
            Supplier(
                id=s_id,
                c=12.0,          # high cost
                co2=4.0,         # low CO2
                cap_nominal=100.0,
                distances=distances,
            )
        )

    # Type B: medium cost, medium CO2
    for i in range(3):
        s_id = f"B{i+1}"
        distances = {b: random.uniform(50, 300) for b in buyer_ids}
        suppliers.append(
            Supplier(
                id=s_id,
                c=10.0,          # medium cost
                co2=7.0,         # medium CO2
                cap_nominal=100.0,
                distances=distances,
            )
        )

    # Type C: low cost, high CO2
    for i in range(3):
        s_id = f"C{i+1}"
        distances = {b: random.uniform(50, 300) for b in buyer_ids}
        suppliers.append(
            Supplier(
                id=s_id,
                c=8.0,           # low cost
                co2=10.0,        # high CO2
                cap_nominal=100.0,
                distances=distances,
            )
        )

    return suppliers


def create_example_buyer() -> Buyer:
    return Buyer(
        id="B1",
        demand_nominal=120.0,
        w_c=1.0,
        w_e=1.0,
        w_f=1.0,
    )
