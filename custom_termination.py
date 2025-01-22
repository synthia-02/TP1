from functools import partial
import gurobipy as gp
from gurobipy import GRB


class CallbackData:
    def __init__(self):
        self.last_gap_change_time = -GRB.INFINITY  # Dernière fois que le gap a changé
        self.last_gap = GRB.INFINITY  # Dernière valeur du gap


def callback(model, where, *, cbdata):
    if where != GRB.Callback.MIP:
        return

    # Vérifiez si une solution réalisable a été trouvée
    sol_count = model.cbGet(GRB.Callback.MIP_SOLCNT)
    if sol_count == 0:
        return

    # Récupérer la meilleure solution réalisable et la borne inférieure
    obj_best = model.cbGet(GRB.Callback.MIP_OBJBST)
    obj_bound = model.cbGet(GRB.Callback.MIP_OBJBND)

    # Calculer le MIPGap
    mip_gap = abs(obj_best - obj_bound) / max(abs(obj_best), abs(obj_bound), 1e-10)

    # Temps d'exécution courant
    current_time = model.cbGet(GRB.Callback.RUNTIME)

    # Si le MIPGap a changé de manière significative
    if abs(cbdata.last_gap - mip_gap) > epsilon_to_compare_gap:
        cbdata.last_gap_change_time = current_time  # Mettre à jour le temps
        cbdata.last_gap = mip_gap  # Mettre à jour le gap

    # Vérifier si le temps écoulé depuis la dernière amélioration dépasse la limite
    if current_time - cbdata.last_gap_change_time > time_from_best:
        print(
            f"Terminating optimization after {time_from_best} seconds without significant MIPGap improvement."
        )
        model.terminate()


# Charger le modèle
with gp.read("data/mkp.mps") as model:
    # Paramètres globaux pour le callback
    time_from_best = 50  # Temps d'attente maximal pour une amélioration
    epsilon_to_compare_gap = 1e-4  # Amélioration minimale significative du gap

    # Initialiser les données pour le callback
    callback_data = CallbackData()
    callback_func = partial(callback, cbdata=callback_data)

    # Résoudre le modèle avec la fonction de rappel
    model.optimize(callback_func)

    # Vérification des résultats
    if model.status == GRB.OPTIMAL:
        print("Solution optimale trouvée.")
    elif model.status == GRB.TIME_LIMIT:
        print("Limite de temps atteinte, solution non optimale.")
    elif model.status == GRB.INTERRUPTED:
        print("Optimisation interrompue par le callback.")
    else:
        print("Aucune solution trouvée ou autre état du modèle.")
