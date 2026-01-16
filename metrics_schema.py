"""
{
  "meta": {
    "scenario_key": "S3",
    "scenario_name": "...",
    "T": 200,
    "tau": 1.0,
    "w_c": 0.3333, "w_e": 0.3333, "w_f": 0.3333,
    "alpha": 0.3333, "beta": 0.3333, "gamma": 0.3333,
    "delta": 0.5,
    "use_individualized_lca": True,
    "use_fairness": True,
    "allocation_mode": "proportional",
    "seed": 42,
  },

  "timeseries": {
    "co2_prod":   [float]*T,
    "co2_trans":  [float]*T,
    "co2_total":  [float]*T,
    "cost_total": [float]*T,
    "allocated_total": [float]*T,   # total allocated per timestep
  },

  "summary": {
    "co2_prod_sum": float,
    "co2_trans_sum": float,
    "co2_total_sum": float,
    "co2_total_mean": float,
    "cost_total_sum": float,
    "cost_total_mean": float,
    "total_allocated": float,     # should be demand*T if feasible
    "share_gini": float,
    "share_max": float,
    "share_std": float,
  },

  "suppliers": {
    "by_id": {
      "A1": {"Q": float, "H": float, "E": float, "F_rot": float, "F_disp": float, "F_uni": float},
      ...
    },
    "by_group": {
      "A": {"Q": float, "H": float},
      "B": {"Q": float, "H": float},
      "C": {"Q": float, "H": float},
    }
  }
}

"""