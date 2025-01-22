import gurobipy as gp
from gurobipy import GRB
import numpy as np

# Données d'entrée
load_forecast = np.array(
    [4, 4, 4, 4, 4, 4, 6, 6, 12, 12, 12, 12, 12, 4, 4, 4, 4, 16, 16, 16, 16, 6.5, 6.5, 6.5]
)
solar_forecast = np.array(
    [0, 0, 0, 0, 0, 0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.5, 3.5, 2.5, 2.0, 1.5, 1.0, 0.5, 0, 0, 0, 0, 0, 0]
)
nTimeIntervals = len(load_forecast)

thermal_units = ["gen1", "gen2", "gen3"]
num_units = len(thermal_units)

# Coûts quadratiques, linéaires, fixes et de démarrage/arrêt
thermal_units_cost = {"gen1": [5.0, 0.5, 1.0, 2, 1], "gen2": [5.0, 0.5, 0.5, 2, 1], "gen3": [5.0, 3.0, 2.0, 2, 1]}
cost_params = np.array([thermal_units_cost[g][:3] for g in thermal_units])
startup_costs = np.array([thermal_units_cost[g][3] for g in thermal_units])
shutdown_costs = np.array([thermal_units_cost[g][4] for g in thermal_units])

# Limites de production
thermal_units_limits = {"gen1": [1.5, 5.0], "gen2": [2.5, 10.0], "gen3": [1.0, 3.0]}
pmin = np.array([thermal_units_limits[g][0] for g in thermal_units])
pmax = np.array([thermal_units_limits[g][1] for g in thermal_units])

# Statut initial
init_status = np.array([0, 0, 0])

# Création du modèle
with gp.Env() as env, gp.Model(env=env) as model:
    # Variables matricielles
    power = model.addMVar((num_units, nTimeIntervals), vtype=GRB.CONTINUOUS, name="power")
    commit = model.addMVar((num_units, nTimeIntervals), vtype=GRB.BINARY, name="commit")
    startup = model.addMVar((num_units, nTimeIntervals), vtype=GRB.BINARY, name="startup")
    shutdown = model.addMVar((num_units, nTimeIntervals), vtype=GRB.BINARY, name="shutdown")

    # Fonction objectif : coût total
    obj = gp.QuadExpr()
    for g in range(num_units):
        obj += (
            cost_params[g, 2] * power[g, :] ** 2
            + cost_params[g, 1] * power[g, :]
            + cost_params[g, 0] * commit[g, :]
            + startup_costs[g] * startup[g, :]
            + shutdown_costs[g] * shutdown[g, :]
        ).sum()
    model.setObjective(obj, GRB.MINIMIZE)

    # Contraintes d'équilibre de puissance
    model.addConstr(
        power.sum(axis=0) + solar_forecast == load_forecast,
        name="power_balance",
    )

    # Contraintes logiques
    logical_lhs = commit[:, 1:] - commit[:, :-1]
    model.addConstr(logical_lhs == startup[:, 1:] - shutdown[:, 1:], name="logical_constraints")

    # Interdire démarrage et arrêt simultanés
    model.addConstr(startup + shutdown <= 1, name="no_simultaneous")

    # Contraintes indicatrices pour les limites physiques
    for g in range(num_units):
        for t in range(nTimeIntervals):
            model.addGenConstrIndicator(commit[g, t], True, power[g, t] >= pmin[g], name=f"min_power_{g}_{t}")
            model.addGenConstrIndicator(commit[g, t], True, power[g, t] <= pmax[g], name=f"max_power_{g}_{t}")
            model.addGenConstrIndicator(commit[g, t], False, power[g, t] == 0, name=f"zero_power_{g}_{t}")

    # Optimisation
    model.optimize()

    # Affichage des résultats
    if model.Status == GRB.OPTIMAL:
        print(f"Coût total : {model.ObjVal:.2f}")
        print("\nRépartition des puissances :")
        for g in range(num_units):
            print(f"Générateur {thermal_units[g]} : {power.x[g]}")
        print("\nEngagement des générateurs :")
        for g in range(num_units):
            print(f"Générateur {thermal_units[g]} : {commit.x[g]}")
