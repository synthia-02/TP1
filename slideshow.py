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

def save_solution(solution, output_path):
    """Sauvegarde la solution au format requis."""
    with open(output_path, 'w') as f:
        f.write(f"{len(solution)}\n")
        for slide in solution:
            f.write(" ".join(map(str, slide)) + "\n")

def compute_final_score(solution, photos):
    """Recalcule le score total de la solution extraite."""
    score = 0
    for i in range(len(solution) - 1):
        tags1 = (photos[solution[i][0]][2] | photos[solution[i][1]][2]) if len(solution[i]) == 2 else photos[solution[i][0]][2]
        tags2 = (photos[solution[i + 1][0]][2] | photos[solution[i + 1][1]][2]) if len(solution[i + 1]) == 2 else photos[solution[i + 1][0]][2]
        score += calculate_score(tags1, tags2)
    return score

def extract_solution(model, horizontal_slides, vertical_pairs, order, photos):
    """Extrait la solution du modèle Gurobi."""
    slides = []
    
    # Ajouter les diapositives horizontales sélectionnées
    for i in horizontal_slides:
        if horizontal_slides[i].x > 0.5:
            slides.append([i])

    # Ajouter les paires de diapositives verticales sélectionnées
    for (i, j) in vertical_pairs:
        if vertical_pairs[i, j].x > 0.5:
            slides.append([i, j])
    
    print(f"Slides générées : {slides}")
    return slides

def create_slideshow_model(photos):
    """Crée et résout un modèle d'optimisation Gurobi."""
    model = Model("Slideshow")
    
    # Variables
    horizontal_slides = {i: model.addVar(vtype=GRB.BINARY, name=f"H_{i}") for i, p in enumerate(photos) if p[1] == 'H'}
    vertical_pairs = {(i, j): model.addVar(vtype=GRB.BINARY, name=f"V_{i}_{j}")
                      for i, j in itertools.combinations([p[0] for p in photos if p[1] == 'V'], 2)}
    
    all_slides = list(horizontal_slides.keys()) + list(vertical_pairs.keys())
    order = {(s1, s2): model.addVar(vtype=GRB.BINARY, name=f"order_{s1}_{s2}") for s1, s2 in itertools.permutations(all_slides, 2)}
    
    # Contraintes : chaque photo ne peut apparaître qu'une seule fois
    for p in range(len(photos)):
        model.addConstr(
            quicksum(horizontal_slides[i] for i in horizontal_slides if i == p) +
            quicksum(vertical_pairs[i, j] for (i, j) in vertical_pairs if i == p or j == p) <= 1,
            f"photo_used_{p}"
        )
    
    # Assurer qu’au moins trois diapositives sont utilisées
    model.addConstr(quicksum(horizontal_slides.values()) + quicksum(vertical_pairs.values()) >= len(photos) // 2, "min_slides")

    # Objectif : maximiser le score des transitions avec un ordonnancement optimal
    model.setObjective(quicksum(
    order[(i, j)] * calculate_score(
        (photos[i[0]][2] | photos[i[1]][2]) if isinstance(i, tuple) else photos[i][2],
        (photos[j[0]][2] | photos[j[1]][2]) if isinstance(j, tuple) else photos[j][2]
    ) for (i, j) in order.keys()
), GRB.MAXIMIZE)


    model.optimize()
    return model, horizontal_slides, vertical_pairs, order

def main():
    if len(sys.argv) != 2:
        print("Usage: python slideshow.py [relative/path/to/dataset]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = os.path.join(os.getcwd(), "slideshow.sol")
    
    photos = load_photos(input_path)
    model, horizontal_slides, vertical_pairs, order = create_slideshow_model(photos)
    solution = extract_solution(model, horizontal_slides, vertical_pairs, order, photos)
    final_score = compute_final_score(solution, photos)
    print(f"Score réel recalculé après optimisation : {final_score}")
    save_solution(solution, output_path)
    print(f"Solution sauvegardée dans {output_path}")
    
if __name__ == "__main__":
    main()
