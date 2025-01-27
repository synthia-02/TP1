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
    """Crée les diapositives valides en respectant les contraintes."""
    horizontal_slides = [(photo[0], photo[2]) for photo in photos if photo[1] == 'H']
    vertical_photos = [photo for photo in photos if photo[1] == 'V']

    # Regrouper les photos verticales par paires pour maximiser les tags combinés
    vertical_pairs = []
    if len(vertical_photos) > 1:
        vertical_pairs = [
            (p1[0], p2[0], p1[2] | p2[2])  # Combine les tags des deux photos
            for p1, p2 in itertools.combinations(vertical_photos, 2)
        ]

    # Convertir les paires verticales en un format uniforme (id, tags)
    vertical_slides = [(p1, p2, tags) for p1, p2, tags in vertical_pairs]

    # Combiner les deux types de diapositives
    return horizontal_slides + vertical_slides



def create_slideshow_model(slides):
    """Crée un modèle Gurobi pour optimiser l'ordre des slides."""
    model = Model("Slideshow")
    model.setParam('OutputFlag', 1)  # Activer les logs

    # Variables : chaque slide peut être utilisé une seule fois
    slide_vars = {i: model.addVar(vtype=GRB.BINARY, name=f"slide_{i}") for i in range(len(slides))}

    # Contraintes : chaque slide est utilisé au maximum une fois
    for i in slide_vars:
        model.addConstr(slide_vars[i] <= 1, name=f"constr_slide_{i}")

    # Objectif : maximiser le score total des transitions
    slide_pairs = list(itertools.combinations(range(len(slides)), 2))
    transitions = {}

    for i, j in slide_pairs:
        tags_i = slides[i][1] if len(slides[i]) == 2 else slides[i][2]  # Tags de la diapositive i
        tags_j = slides[j][1] if len(slides[j]) == 2 else slides[j][2]  # Tags de la diapositive j
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
    photos = load_photos(input_path)
    slides = create_slides(photos)
    model, slide_vars = create_slideshow_model(slides)
    solution = generate_solution(model, slide_vars)
    save_solution(solution, slides, output_path)
    print(f"Solution sauvegardée dans {output_path}")


if __name__ == "__main__":
    main()
