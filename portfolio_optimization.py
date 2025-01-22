import json
import pandas as pd
import numpy as np
import gurobipy as gp
from gurobipy import GRB

# Charger les données depuis portfolio-example.json
with open("portfolio-example.json", "r") as f:
    data = json.load(f)

# Extraire les paramètres
n = data["num_assets"]
sigma = np.array(data["covariance"])
mu = np.array(data["expected_return"])
mu_0 = data["target_return"]
k = data["portfolio_max_size"]

# Modélisation et optimisation
with gp.Model("portfolio") as model:
    x = model.addVars(n, vtype=GRB.CONTINUOUS, lb=0, ub=1, name="x")
    y = model.addVars(n, vtype=GRB.BINARY, name="y")

    # Objectif : Minimiser le risque
    risk = gp.quicksum(sigma[i, j] * x[i] * x[j] for i in range(n) for j in range(n))
    model.setObjective(risk, GRB.MINIMIZE)

    # Contraintes
    model.addConstr(gp.quicksum(mu[i] * x[i] for i in range(n)) >= mu_0, name="return")
    model.addConstr(gp.quicksum(x[i] for i in range(n)) == 1, name="budget")
    model.addConstr(gp.quicksum(y[i] for i in range(n)) <= k, name="max_assets")
    for i in range(n):
        model.addConstr(x[i] <= y[i], name=f"link_{i}")

    model.optimize()

    # Vérification des résultats
    if model.status == GRB.OPTIMAL:
        portfolio = [x[i].X for i in range(n)]
        total_risk = model.ObjVal
        total_return = sum(mu[i] * portfolio[i] for i in range(n))

        # Affichage des résultats
        print("\n=== Résultats ===")
        print(f"Risque total : {total_risk:.4f}")
        print(f"Rendement total : {total_return:.4f}")
        print("Répartition du portefeuille :")
        for i in range(n):
            if portfolio[i] > 0:
                print(f"  Actif {i}: {portfolio[i]:.4f}")

        # Écrire les résultats dans un fichier
        with open("portfolio_results.txt", "w") as f:
            f.write("=== Résultats de l'optimisation de portefeuille ===\n\n")
            f.write(f"Risque total : {total_risk:.4f}\n")
            f.write(f"Rendement total : {total_return:.4f}\n")
            f.write("Répartition du portefeuille :\n")
            for i in range(n):
                if portfolio[i] > 0:
                    f.write(f"  Actif {i}: {portfolio[i]:.4f}\n")
        print("Résultats écrits dans portfolio_results.txt")
    else:
        print("Aucune solution optimale trouvée.")
