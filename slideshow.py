from gurobipy import Model, GRB, quicksum
import sys

def main(dataset_path):
    # Charger le dataset
    with open(dataset_path, 'r') as file:
        N = int(file.readline().strip())
        photos = []
        for i in range(N):
            parts = file.readline().strip().split()
            orientation = parts[0]
            tags = set(parts[2:])
            photos.append({'id': i, 'orientation': orientation, 'tags': tags})

    # Créer le modèle
    model = Model("Slideshow")
    model.setParam('OutputFlag', 1)
    model.setParam('TimeLimit', 600)

    # Variables de décision pour les diapositives
    s = []  # Liste de variables binaires pour savoir si une diapositive est sélectionnée
    slide_tags = []  # Liste pour les tags de chaque diapositive
    slide_indices = []  # Liste pour conserver les indices des diapositives

    # Créer les diapositives pour les photos horizontales
    for i in range(N):
        if photos[i]['orientation'] == 'H':
            slide_id = len(s)
            s.append(model.addVar(vtype=GRB.BINARY, name=f"s_{slide_id}"))
            slide_tags.append(photos[i]['tags'])
            slide_indices.append(i)  # Conserver l'index de la photo horizontale

    # Créer les diapositives pour les photos verticales
    for i in range(N):
        for j in range(i + 1, N):
            if photos[i]['orientation'] == 'V' and photos[j]['orientation'] == 'V':
                slide_id = len(s)
                s.append(model.addVar(vtype=GRB.BINARY, name=f"s_{slide_id}"))
                slide_tags.append(photos[i]['tags'].union(photos[j]['tags']))
                slide_indices.append((i, j))  # Conserver les indices des photos verticales

    # Variables pour les transitions
    transitions = [model.addVar(vtype=GRB.INTEGER, name=f"transition_{i}") for i in range(len(slide_tags) - 1)]

    # Objectif : Maximiser le score total
    model.setObjective(quicksum(transitions), GRB.MAXIMIZE)

    # Contraintes pour les transitions
    for i in range(len(transitions)):
        common_tags = slide_tags[i].intersection(slide_tags[i + 1])
        tags_only_in_current = slide_tags[i].difference(slide_tags[i + 1])
        tags_only_in_next = slide_tags[i + 1].difference(slide_tags[i])
        interest = min(len(common_tags), len(tags_only_in_current), len(tags_only_in_next))
        model.addConstr(transitions[i] == interest)

    # Le diaporama doit avoir au moins une diapositive
    model.addConstr(quicksum(s) >= 1, name="at_least_one_slide")

    # Optimiser
    model.optimize()

    # Vérifier l'objectif
    if model.status == GRB.OPTIMAL:
        selected_slides = [i for i in range(len(s)) if s[i].X > 0.5]

        # Calculer le score total
        total_interest = 0
        for i in range(len(selected_slides) - 1):
            current_tags = slide_tags[selected_slides[i]]
            next_tags = slide_tags[selected_slides[i + 1]]
            common = len(current_tags.intersection(next_tags))
            only_current = len(current_tags.difference(next_tags))
            only_next = len(next_tags.difference(current_tags))
            total_interest += min(common, only_current, only_next)

        print(f"Objective (from Gurobi): {model.objVal}")
        print(f"Recalculated objective: {total_interest}")

        # Exporter la solution
        with open('slideshow.sol', 'w') as file:
            file.write(f"{int(model.objVal)}\n")
            file.write(f"{len(selected_slides)}\n")  # Ajout du nombre total de diapositives
            used_photos = set()  # Ensemble pour suivre les photos déjà utilisées
            for slide_id in selected_slides:
                photos_in_slide = []
                if slide_id < len(slide_indices):  # Vérification correcte de l'index
                    if isinstance(slide_indices[slide_id], int):
                        photo_id = slide_indices[slide_id]
                        if photo_id not in used_photos:
                            photos_in_slide.append(str(photo_id))
                            used_photos.add(photo_id)
                    else:
                        # Diapositive de deux photos verticales
                        for photo_id in slide_indices[slide_id]:
                            if photo_id not in used_photos:
                                photos_in_slide.append(str(photo_id))
                                used_photos.add(photo_id)
                file.write(" ".join(photos_in_slide) + "\n")

    else:
        print("Aucune solution trouvée. Statut du modèle :", model.status)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python slideshow.py [dataset_path]")
        sys.exit(1)
    main(sys.argv[1])



