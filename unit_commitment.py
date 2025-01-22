import gurobipy as gp
from gurobipy import GRB

# 24 Hour Load Forecast (MW)
load_forecast = [
    4, 4, 4, 4, 4, 4, 6, 6, 12, 12, 12, 12, 12, 4, 4, 4, 4, 16, 16, 16, 16, 6.5, 6.5, 6.5,
]

# Solar energy forecast (MW)
solar_forecast = [
    0, 0, 0, 0, 0, 0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.5, 3.5, 2.5, 2.0, 1.5, 1.0, 0.5, 0, 0, 0, 0, 0, 0,
]

# Number of time intervals
nTimeIntervals = len(load_forecast)

# Thermal units
thermal_units = ["gen1", "gen2", "gen3"]

# Thermal units' costs and startup/shutdown costs
thermal_units_cost, a, b, c, sup_cost, sdn_cost = gp.multidict(
    {"gen1": [5.0, 0.5, 1.0, 2, 1], "gen2": [5.0, 0.5, 0.5, 2, 1], "gen3": [5.0, 3.0, 2.0, 2, 1]}
)

# Thermal units operating limits
thermal_units_limits, pmin, pmax = gp.multidict(
    {"gen1": [1.5, 5.0], "gen2": [2.5, 10.0], "gen3": [1.0, 3.0]}
)

# Initial commitment status
thermal_units_dyn_data, init_status = gp.multidict(
    {"gen1": [0], "gen2": [0], "gen3": [0]}
)


def show_results():
    obj_val_s = model.ObjVal
    print(f"Overall Cost = {round(obj_val_s, 2)}")
    print("\n%5s" % "time", end=" ")
    for t in range(nTimeIntervals):
        print("%4s" % t, end=" ")
    print("\n")

    for g in thermal_units:
        print("%5s" % g, end=" ")
        for t in range(nTimeIntervals):
            print("%4.1f" % thermal_units_out_power[g, t].X, end=" ")
        print("\n")

    print("%5s" % "Solar", end=" ")
    for t in range(nTimeIntervals):
        print("%4.1f" % solar_forecast[t], end=" ")
    print("\n")

    print("%5s" % "Load", end=" ")
    for t in range(nTimeIntervals):
        print("%4.1f" % load_forecast[t], end=" ")
    print("\n")


# Gurobi model
with gp.Env() as env, gp.Model(env=env) as model:
    # Variables for thermal units (power, commitment, startup, shutdown)
    thermal_units_out_power = model.addVars(
        thermal_units, range(nTimeIntervals), vtype=GRB.CONTINUOUS, name="out_power"
    )
    thermal_units_startup_status = model.addVars(
        thermal_units, range(nTimeIntervals), vtype=GRB.BINARY, name="startup_status"
    )
    thermal_units_shutdown_status = model.addVars(
        thermal_units, range(nTimeIntervals), vtype=GRB.BINARY, name="shutdown_status"
    )
    thermal_units_comm_status = model.addVars(
        thermal_units, range(nTimeIntervals), vtype=GRB.BINARY, name="comm_status"
    )

    # Objective function: minimize total cost
    obj_fun_expr = gp.QuadExpr()
    for t in range(nTimeIntervals):
        for g in thermal_units:
            obj_fun_expr += (
                c[g] * thermal_units_out_power[g, t] ** 2
                + b[g] * thermal_units_out_power[g, t]
                + a[g] * thermal_units_comm_status[g, t]
                + sup_cost[g] * thermal_units_startup_status[g, t]
                + sdn_cost[g] * thermal_units_shutdown_status[g, t]
            )
    model.setObjective(obj_fun_expr, GRB.MINIMIZE)

    # Power balance constraints
    for t in range(nTimeIntervals):
        model.addConstr(
            gp.quicksum(thermal_units_out_power[g, t] for g in thermal_units)
            + solar_forecast[t]
            == load_forecast[t],
            name=f"power_balance_{t}",
        )

    # Thermal unit logical constraints
    for t in range(nTimeIntervals):
        for g in thermal_units:
            if t == 0:
                model.addConstr(
                    thermal_units_comm_status[g, t] - init_status[g]
                    == thermal_units_startup_status[g, t]
                    - thermal_units_shutdown_status[g, t],
                    name=f"logical1_{g}_{t}",
                )
            else:
                model.addConstr(
                    thermal_units_comm_status[g, t] - thermal_units_comm_status[g, t - 1]
                    == thermal_units_startup_status[g, t]
                    - thermal_units_shutdown_status[g, t],
                    name=f"logical1_{g}_{t}",
                )
            model.addConstr(
                thermal_units_startup_status[g, t] + thermal_units_shutdown_status[g, t] <= 1,
                name=f"logical2_{g}_{t}",
            )

    # Thermal unit physical constraints using indicator constraints
    for t in range(nTimeIntervals):
        for g in thermal_units:
            model.addGenConstrIndicator(
                thermal_units_comm_status[g, t],
                True,
                thermal_units_out_power[g, t] >= pmin[g],
                name=f"indicator_min_{g}_{t}",
            )
            model.addGenConstrIndicator(
                thermal_units_comm_status[g, t],
                True,
                thermal_units_out_power[g, t] <= pmax[g],
                name=f"indicator_max_{g}_{t}",
            )
            model.addGenConstrIndicator(
                thermal_units_comm_status[g, t],
                False,
                thermal_units_out_power[g, t] == 0,
                name=f"indicator_zero_{g}_{t}",
            )

    # Optimize the model
    model.optimize()
    show_results()
