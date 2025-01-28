import sys
from gurobipy import Model, GRB, quicksum
import itertools
import os


def load_photos(file_path):
    """Charge les photos à partir d'un fichier de dataset."""
    with open(file_path, 'r') as f:
        lines = f.readlines()
    num_photos = int(lines[0].strip())
    photos = []
    for i, line in enumerate(lines[1:]):
        parts = line.strip().split()
        orientation = parts[0]
        tags = set(parts[2:])
        photos.append((i, orientation, tags))
    return photos


def calculate_score(tags1, tags2):
    """Calcule le score entre deux ensembles de tags."""
    common_tags = len(tags1 & tags2)
    unique_in_1 = len(tags1 - tags2)
    unique_in_2 = len(tags2 - tags1)
    return min(common_tags, unique_in_1, unique_in_2)


def create_slides(photos):
    """Crée des diapositives valides en respectant les contraintes."""
    # Diapositives horizontales
    horizontal_slides = [(photo[0], photo[2]) for photo in photos if photo[1] == 'H']

    # Diapositives verticales
    vertical_photos = [photo for photo in photos if photo[1] == 'V']
    vertical_slides = []
    
    # Associer les photos verticales par paires
    used_verticals = set()
    for i, p1 in enumerate(vertical_photos):
        if p1[0] in used_verticals:
            continue
        for j, p2 in enumerate(vertical_photos):
            if i != j and p2[0] not in used_verticals:
                # Créer une diapositive combinée
                vertical_slides.append((p1[0], p2[0], p1[2] | p2[2]))
                used_verticals.add(p1[0])
                used_verticals.add(p2[0])
                break  # Trouver une seule paire

    # Combiner les diapositives horizontales et verticales
    return horizontal_slides + vertical_slides


def create_slideshow_model(slides, photos):
    """Crée un modèle Gurobi pour optimiser l'ordre des diapositives."""
    model = Model("Slideshow")
    model.setParam('OutputFlag', 1)  # Activer les logs pour voir les détails

    # Variable binaire pour chaque slide
    slide_vars = {i: model.addVar(vtype=GRB.BINARY, name=f"slide_{i}") for i in range(len(slides))}

    # Contraintes : chaque photo est utilisée au maximum une fois
    photo_used = {photo[0]: [] for photo in photos}
    for i, slide in enumerate(slides):
        if len(slide) == 2:  # Diapositive horizontale
            photo_used[slide[0]].append(slide_vars[i])
        elif len(slide) == 3:  # Diapositive verticale
            photo_used[slide[0]].append(slide_vars[i])
            photo_used[slide[1]].append(slide_vars[i])

    for photo_id, vars_list in photo_used.items():
        model.addConstr(quicksum(vars_list) <= 1, name=f"photo_{photo_id}_used_once")

    # Objectif : maximiser le score total des transitions
    slide_pairs = list(itertools.combinations(range(len(slides)), 2))
    transitions = {}
    for i, j in slide_pairs:
        tags_i = slides[i][1] if len(slides[i]) == 2 else slides[i][2]
        tags_j = slides[j][1] if len(slides[j]) == 2 else slides[j][2]
        transitions[(i, j)] = calculate_score(tags_i, tags_j)

    model.setObjective(
        quicksum(transitions[i, j] * slide_vars[i] * slide_vars[j] for i, j in transitions.keys()),
        GRB.MAXIMIZE,
    )

    return model, slide_vars


def save_solution(solution, slides, output_path):
    """Sauvegarde la solution dans un fichier .sol."""
    with open(output_path, 'w') as f:
        f.write(f"{len(solution)}\n")
        for slide in solution:
            if len(slides[slide]) == 2:
                f.write(f"{slides[slide][0]}\n")
            elif len(slides[slide]) == 3:
                f.write(f"{slides[slide][0]} {slides[slide][1]}\n")


def generate_solution(model, slide_vars):
    """Optimise le modèle et génère une solution."""
    model.optimize()
    if model.status == GRB.OPTIMAL:
        return [i for i, var in slide_vars.items() if var.x > 0.5]
    else:
        print("Aucune solution optimale trouvée.")
        return []


def main():
    if len(sys.argv) != 2:
        print("Usage: python slideshow.py [relative/path/to/dataset]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = os.path.join(os.getcwd(), "slideshow.sol")
    
    # Charger les données
    photos = load_photos(input_path)
    
    # Créer les diapositives
    slides = create_slides(photos)
    
    # Créer et résoudre le modèle Gurobi
    model, slide_vars = create_slideshow_model(slides, photos)
    solution = generate_solution(model, slide_vars)
    
    # Sauvegarder la solution
    save_solution(solution, slides, output_path)
    print(f"Solution sauvegardée dans {output_path}")


if __name__ == "__main__":
    main()
