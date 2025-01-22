import numpy as np
import gurobipy as gp
from gurobipy import GRB

def generate_knapsack(num_items):
    rng = np.random.default_rng(seed=0)
    values = rng.uniform(low=1, high=25, size=num_items)
    weights = rng.uniform(low=5, high=100, size=num_items)
    capacity = 0.7 * weights.sum()
    return values, weights, capacity

def solve_knapsack_model(values, weights, capacity):
    num_items = len(values)
    values_dict = {i: values[i] for i in range(num_items)}
    weights_dict = {i: weights[i] for i in range(num_items)}

    with gp.Env() as env:
        with gp.Model(name="knapsack", env=env) as model:
            x = model.addVars(num_items, vtype=GRB.BINARY, name="x")
            model.setObjective(x.prod(values_dict), GRB.MAXIMIZE)
            model.addConstr(x.prod(weights_dict) <= capacity, "capacity")
            model.optimize()

            if model.status == GRB.OPTIMAL:
                selected_items = [i for i in range(num_items) if x[i].x > 0.5]
                total_value = sum(values[i] for i in selected_items)
                total_weight = sum(weights[i] for i in selected_items)

                # Écrire les résultats dans un fichier
                with open("results.txt", "w") as f:
                    f.write("=== Résultats du problème du sac à dos ===\n\n")
                    f.write(f"Valeur optimale : {total_value:.2f}\n")
                    f.write(f"Poids total des objets sélectionnés : {total_weight:.2f}\n")
                    f.write(f"Capacité du sac à dos : {capacity:.2f}\n\n")
                    f.write("Indices des objets sélectionnés :\n")
                    f.write(f"{selected_items}\n")

                print("Résultats écrits dans results.txt")
            else:
                print("Aucune solution optimale trouvée.")

if __name__ == "__main__":
    num_items = 10000
    values, weights, capacity = generate_knapsack(num_items)
    solve_knapsack_model(values, weights, capacity)
