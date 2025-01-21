import numpy as np
import gurobipy as gp
from gurobipy import GRB

def generate_knapsack(num_items):
    # Fixer la graine pour la reproductibilité
    rng = np.random.default_rng(seed=0)
    # Valeurs et poids des objets
    values = rng.uniform(low=1, high=25, size=num_items)
    weights = rng.uniform(low=5, high=100, size=num_items)
    # Capacité du sac à dos
    capacity = 0.7 * weights.sum()
    return values, weights, capacity

def solve_knapsack_model(values, weights, capacity):
    num_items = len(values)
    items = range(num_items)
    # Créer un modèle Gurobi
    model = gp.Model("knapsack")
    # Ajouter les variables binaires
    x = model.addVars(items, vtype=GRB.BINARY, name="x")
    # Définir la fonction objectif
    model.setObjective(gp.quicksum(values[i] * x[i] for i in items), GRB.MAXIMIZE)
    # Ajouter la contrainte de capacité
    model.addConstr(gp.quicksum(weights[i] * x[i] for i in items) <= capacity, name="capacity")
    # Optimiser le modèle
    model.optimize()
    # Afficher les résultats
    if model.status == GRB.OPTIMAL:
        selected_items = [i for i in items if x[i].x > 0.5]
        total_value = sum(values[i] for i in selected_items)
        total_weight = sum(weights[i] for i in selected_items)
        print(f"Total value: {total_value}")
        print(f"Total weight: {total_weight}")
        print(f"Selected items: {selected_items}")
    else:
        print("No optimal solution found.")

if __name__ == "__main__":
    num_items = 10000  # Nombre d'objets
    values, weights, capacity = generate_knapsack(num_items)
    solve_knapsack_model(values, weights, capacity)
