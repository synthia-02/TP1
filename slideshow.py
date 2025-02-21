import sys
from gurobipy import Model, GRB

class Photo:
    def __init__(self, lid, tags, orientation):
        self.id = lid
        self.tags = set(tags)
        self.orientation = orientation

class Slide:
    def __init__(self, photos):
        self.photos = photos
        self.tags = set()
        for photo in photos:
            self.tags.update(photo.tags)
    
    def get_id(self):
        return " ".join(str(photo.id) for photo in self.photos)

def read_input(file_path):
    """ Lit le fichier d'entrée et stocke les photos. """
    photos = []
    with open(file_path, "r") as f:
        num_photos = int(f.readline().strip())
        for i in range(num_photos):
            data = f.readline().strip().split()
            orientation = data[0]
            tags = data[2:]
            photos.append(Photo(i, tags, orientation))
    return photos

def count_score(tags1, tags2):
    """ Calcule le score entre deux slides. """
    common_tags = len(tags1 & tags2)
    unique_tags1 = len(tags1 - tags2)
    unique_tags2 = len(tags2 - tags1)
    return min(common_tags, unique_tags1, unique_tags2)

def create_slides(photos):
    """ Génère les slides horizontaux et les paires verticales. """
    slides = []
    vertical_photos = [p for p in photos if p.orientation == 'V']
    horizontal_photos = [p for p in photos if p.orientation == 'H']

    for photo in horizontal_photos:
        slides.append(Slide([photo]))

    for i in range(0, len(vertical_photos) - 1, 2):
        slides.append(Slide([vertical_photos[i], vertical_photos[i + 1]]))

    return slides

def optimize_slideshow(slides):
    """ Utilise Gurobi pour optimiser l'ordre des slides. """
    model = Model("SlideshowOptimization")
    num_slides = len(slides)

    x = model.addVars(num_slides, num_slides, vtype=GRB.BINARY, name="x")

    model.setObjective(
        sum(x[i, j] * count_score(slides[i].tags, slides[j].tags)
            for i in range(num_slides) for j in range(num_slides) if i != j),
        GRB.MAXIMIZE
    )

    for i in range(num_slides):
        model.addConstr(sum(x[i, j] for j in range(num_slides) if i != j) == 1)
        model.addConstr(sum(x[j, i] for j in range(num_slides) if i != j) == 1)

    model.optimize()

    slideshow = []
    for i in range(num_slides):
        for j in range(num_slides):
            if i != j and x[i, j].x > 0.5:
                slideshow.append(slides[i])

    return slideshow

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python slideshow.py <input_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    photos = read_input(input_file)
    slides = create_slides(photos)
    slideshow = optimize_slideshow(slides)

    with open("slideshow.sol", "w") as f:
        f.write(f"{len(slideshow)}\n")
        for slide in slideshow:
            f.write(slide.get_id() + "\n")

    print("Solution générée dans slideshow.sol")
