"""
    Projet IA
        “Algorithmes génétiques”

        Alexandre Perez
        Sébastion Vaucher
        HE-Arc 2014

    ----------------------------

    Le codage des individus est de type à caractères multiples. L'algorithme commence donc par initialiser la population
    de base avec comme taille 1000% du nombre de ville de départ. (500 pour 50 villes) Après évaluation de toutes ces
    solutions, la meilleure est choisie. Puis tant que la meilleure solution n'est pas battue durant 50 fois génération,
    l'algorithme effectue :
    1. Sélection :
        Choisie 30% de la population, les meilleures d'entre eux. Cependant pour éviter de tomber dans un minimum local
        on ne choisira pas des solutions similaires (dans la distance totale varie de moins de 1 e-6)
    2. Croisement :
        Croisement en deux points, tirage de deux point aléatoire et on remplace le chemin entre les deux points de la
        première solution par ceux de la deuxième et inversement.
    3. Mutation :
        Mutation avec la méthode 2opt, ou deux liaisons sont tirées au sort, puis si l'ordre dont sont relier ces 4
        points (deux côté, donc 4 points) est meilleurs en les inversant alors on mute en les inversant et
        en inversant le chemin en eux aussi.
    4. Test si une meilleure solution existe dans la nouvelle population et recommence au point 1.
"""
import pygame
import math
import random
import sys
import time
from pygame.locals import KEYDOWN, QUIT, MOUSEBUTTONDOWN, K_RETURN

# GUI
screen = None
city_color = (10, 10, 200)  # blue
summary_color = (255, 255, 255)
city_font_size = 16  # pixels
summary_font_size = 26
screen_size = (500, 500)
city_radius = 2
city_font = None
summary_font = None

cities = []
# Population size percent from the number of cities, here 1000%
population_size_percent = 1000 / 100
# Quantity of elite for the selection, here 30% of the population
elitism_percent = 30 / 100
# Quantity of solution that we will mutate, here 20% of the population
mutation_percent = 20 / 100
# Size of the tournament
tournament_size = 15
# Limit for stop generation if no better solution found
gen_without_better_solution_limit = 50
# Limit a mutation try before skip it
limit_mutation_try = 10


def cities_from_file(file):
    f = open(file, 'r')
    cities.clear()
    for line in f:
        comp = line.rstrip('\n').split(' ')
        city = (comp[0], (int(comp[1]), int(comp[2])))
        cities.append(city)

    return cities


def draw_cities(positions, connected=False, generation=-1, distance=-1):
    if screen is not None:
        screen.fill(0)
        for pos in positions:
            text = city_font.render(pos[0], True, city_color, (0, 0, 0))
            textrect = text.get_rect()
            textrect.centerx = pos[1][0]
            textrect.centery = pos[1][1]
            screen.blit(text, textrect)

        if connected:
            pygame.draw.lines(screen, city_color, True, [x[1] for x in positions])

        if generation != -1 and distance != -1:
            text = city_font.render('Generation n°' + str(generation) + '; Distance = ' + str(round(distance, 2)), True,
                                    summary_color, (0, 0, 0))
            textrect = text.get_rect()
            textrect.centerx = screen_size[0] / 2.0
            textrect.centery = screen_size[1] - summary_font_size / 4.0
            screen.blit(text, textrect)

        pygame.display.flip()


def setup_gui():
    global screen, city_font, summary_font
    pygame.init()
    city_font = pygame.font.SysFont(None, city_font_size)
    summary_font = pygame.font.SysFont(None, summary_font_size)
    pygame.display.set_mode(screen_size)
    pygame.display.set_caption('TSP by Alexandre Perez and Sébastien Vaucher')
    screen = pygame.display.get_surface()


def cities_by_mouse():
    global screen
    was_gui = True
    if screen is None:
        was_gui = False
        setup_gui()

    collecting = True
    i = 0
    while collecting:
        for event in pygame.event.get():
            if event.type == QUIT:
                sys.exit(0)
            elif event.type == KEYDOWN and event.key == K_RETURN:
                collecting = False
            elif event.type == MOUSEBUTTONDOWN:
                city = ('v' + str(i), pygame.mouse.get_pos())
                i += 1
                cities.append(city)
                draw_cities(cities)

    if not was_gui:
        pygame.quit()
        screen = None


def ga_solve(file=None, gui=True, maxtime=0):
    global cities
    t1 = time.time()

    if gui:
        setup_gui()

    if file is not None:
        cities = cities_from_file(file)
    else:
        cities_by_mouse()

    draw_cities(cities)

    quantity_of_cities = len(cities)
    population_size = quantity_of_cities * population_size_percent
    # population_size = min(population_size, len(cities) * (len(cities) + 1) / 2)

    # Initial population
    population = initial_population(cities, population_size)

    gen = 0
    gen_without_better_solution = 0
    fittest = None

    while (maxtime == 0 and gen_without_better_solution < gen_without_better_solution_limit) or time.time() - t1 <= maxtime:
        if screen is not None:
            for event in pygame.event.get():
                if event.type == QUIT:
                    sys.exit(0)

        # Evaluate
        # evaluate(population) No need to evaluate because score is always computed when new solution is done, just sort it
        population.sort(key=lambda s: s[1])
        # Check the fittest
        if fittest is None or fittest[1] > population[0][1]:
            gen_without_better_solution = 0
            #print("gen : ", gen)
            fittest = [population[0][0].copy(), population[0][1]]
        draw_cities(fittest[0], True, gen, fittest[1])

        # If the quantity of cities is less than 7,
        # we don't make crossover. We just mutate on all the population
        if quantity_of_cities > 6:
            # Selection
            elites = selection(population)
            # Crossover
            children = crossover(elites, population_size - len(elites))
            population = elites + children

        # Mutate
        for i in range(0, int(len(population) * mutation_percent)):
            mutate(population[random.randint(0, len(population) - 1)][0])
        gen += 1
        gen_without_better_solution += 1
        #print((time.time() - t1) / gen)

    return total_distance(fittest[0]), [c[0] for c in fittest[0]]


def evaluate(population):
    """
    Evaluate all solutions of the population.
    """
    for solution in population:
        solution[1] = total_distance(solution[0])


def selection(population):
    """
    Call the selection method
    """
    elite_quantity = int(len(cities) * elitism_percent)
    #return selection_elites(population, elite_quantity)
    #return selection_tournament(population, elite_quantity)
    return selection_SENGOKU(population, elite_quantity)


def crossover(subpopulation, quantity):
    """
    Call the crossover method
    """
    return crossover_two_points(subpopulation, quantity)


def mutate(solution):
    """
    Call the mutation method
    """
    #mutate_swap(solution)
    mutate_2opt(solution)
    #mutate_reverse(solution)


def selection_elites(population, elite_quantity):
    """
    Return the best N solution from population. Where N = elite_quantity
    """
    return [population[i] for i in range(0, elite_quantity)]


def selection_tournament(population, elite_quantity):
    """
    Return N solution from population by apply a tournament selection. Where N = elite_quantity
    We take X(tournament_size) solution from the population, then we save the best solution, and delete it from the population.
    We return all solution saved.
    """
    winners = []
    for i in range(0, elite_quantity):
        competitors = []
        for j in range(0, tournament_size):
            competitor = population[random.randint(0, len(population) - 1)]
            while competitor in competitors:
                competitor = population[random.randint(0, len(population) - 1)]
            competitors.append(competitor)
        competitors.sort(key=lambda s: s[1])
        winners.append(competitors[0])
        population.remove(competitors[0])
    return winners


def selection_SENGOKU(population, elite_quantity):
    """
    Return N solution from population by apply a natural selection. Where N = elite_quantity
    We want the best. For keep the diversity of the population, we remove all similar solutions.
    By removing the similar solutions, we won't go to a local minima.
    """
    i = 1
    while i < len(population):
        if is_solutions_similar(population[i - 1], population[i]):
            del population[i]
        else:
            i += 1
    while len(population) > elite_quantity:
        del population[-1]
    return population


def crossover_two_points(subpopulation, quantity):
    """
    Apply the two points crossover function on the subpopulation.
    Return N new solution. Where N = quantity
    """
    crossed = []
    while len(crossed) < quantity:
        s1 = subpopulation[random.randint(0, len(subpopulation) - 1)]
        s2 = s1
        while s1 == s2:
            s2 = subpopulation[random.randint(0, len(subpopulation) - 1)]
        p1 = random.randint(1, len(s1[0]) - 2)
        p2 = p1
        while p1 == p2:
            p2 = random.randint(1, len(s2[0]) - 2)
        if p1 > p2:
            temp = p2
            p2 = p1
            p1 = temp

        children = cross_two_solutions(s1[0].copy(), s2[0].copy(), p1, p2)

        crossed += children

    if len(crossed) > quantity:
        return crossed[:-1]
    return crossed


def cross_two_solutions(solution1, solution2, p1, p2):
    """
    Apply a crossover with the two solutions passed in parameter.
    Return two new solutions from the parent (One if the two are the same)
    """
    middle_cities1 = solution1[p1:p2]
    middle_cities2 = solution2[p1:p2]

    pack_cities(solution1, middle_cities2, p1, p2)
    pack_cities(solution2, middle_cities1, p1, p2)

    for i in range(p1, p2):
        solution1[i] = middle_cities2[i - p1]
        solution2[i] = middle_cities1[i - p1]

    solution1 = [solution1, total_distance(solution1)]
    solution2 = [solution2, total_distance(solution2)]

    if is_solutions_equal(solution1, solution2):
        return [solution1]
    return [solution1, solution2]


def pack_cities(solution, middle_cities, p1, p2):
    """
    Pack all the cities to a to the right of the p2 point.
    Then all points between p1 and p2 are None.
    """
    for i in range(0, len(solution)):
        if solution[i] in middle_cities:
            solution[i] = None
    i = p2
    while i != p1:
        if solution[i] is None:
            j = i + 1
            while j >= len(solution) - 1 or solution[j] is None:
                if j >= len(solution) - 1:
                    j = 0
                else:
                    j += 1
            solution[i] = solution[j]
            solution[j] = None
        if i >= len(solution) - 1:
            i = 0
        else:
            i += 1


def mutate_swap(solution):
    """
    Just swap two randoms points of the solution
    """
    p1 = random.randint(0, len(solution) - 1)
    p2 = p1
    while p1 == p2:
        p2 = random.randint(0, len(solution) - 1)
    temp = solution[p1]
    solution[p1] = solution[p2]
    solution[p2] = temp


def mutate_2opt(solution):
    """
    Take two random edge, and check if we reverse the path between points of the edges improve out solution.
    If it's improved, then do the mutation
    """
    improved = False
    mutation_try = 0
    while not improved and mutation_try < limit_mutation_try:
        p1 = random.randint(0, len(solution) - 1)
        p2 = p1 + 1 if p1 + 1 < len(solution) else 0
        p3, p4 = p1, p2
        while abs(p1 - p3) < 2 or abs(p2 - p4) < 2:
            p3 = random.randint(0, len(solution) - 1)
            p4 = p3 + 1 if p3 + 1 < len(solution) else 0
        if distance_between(solution[p1], solution[p2]) + distance_between(solution[p3],solution[p4]) > \
                        distance_between(solution[p1], solution[p3]) + distance_between(solution[p2], solution[p4]):
            solution[p2], solution[p3] = solution[p3], solution[p2]
            reverse(solution, p2, p3)
            improved = True
        elif distance_between(solution[p1], solution[p2]) + distance_between(solution[p3], solution[p4]) > \
                        distance_between(solution[p1], solution[p4]) + distance_between(solution[p3], solution[p2]):
            solution[p2], solution[p4] = solution[p4], solution[p2]
            reverse(solution, p2, p4)
            improved = True
        mutation_try += 1


def mutate_reverse(solution):
    """
    Mutate just by reverse a path between two random points
    """
    p1 = random.randint(0, len(solution) - 1)
    p2 = p1
    while p1 == p2:
        p2 = random.randint(0, len(solution) - 1)
    reverse(solution, p1, p2)


def reverse(solution, p1, p2):
    """
    Reverse the path between the two points in the given solution
    """
    trip = solution[p1:p2] if p1 < p2 else solution[p1:] + solution[:p2]
    while p1 != p2:
        solution[p1] = trip.pop()
        p1 = p1 + 1 if p1 + 1 < len(solution) else 0


def is_solutions_similar(solution1, solution2):
    """
    Compare if the two solutions are similar
    """
    return abs(solution1[1] - solution2[1]) < 1e-6


def is_solutions_equal(solution1, solution2):
    """
    Compare if the two solutions are equal
    """
    for i in range(0, len(solution1)):
        if solution1[0][i][0] != solution2[0][i][0]:
            return False
    return True


def total_distance(solution):
    """
    Return total distance between all cities, with the distance front the last and the first
    """
    distance = 0
    c2 = None
    for c in solution:
        c1 = c2
        c2 = c
        if c1 is not None and c2 is not None:
            distance += distance_between(c1, c2)

    distance += distance_between(solution[0], solution[len(solution) - 1])
    return distance


def distance_between(city1, city2):
    """
    Return the distance between two cities
    """
    return math.sqrt((city1[1][0] - city2[1][0]) * (city1[1][0] - city2[1][0]) +
                     (city1[1][1] - city2[1][1]) * (city1[1][1] - city2[1][1]))


def is_solution_in_population(solution, population):
    """
    Return true if the solution is in the population
    """
    return any(abs(sol[1] - solution[1]) < 1e-9 for sol in population)


def initial_population(cities, quantity):
    """
    Create the initial population from the cities passed in parameter.
    Each solution is a shuffle of the cities set
    """
    population = []
    while len(population) < quantity:
        solution = cities.copy()
        random.shuffle(solution)
        solution = [solution, total_distance(solution)]
        population.append(solution)
    return population


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Voyageur de commerce')
    parser.add_argument('--nogui', default=True, action='store_false')
    parser.add_argument('--maxtime', type=int, default=0)
    parser.add_argument('filename', nargs='?', default=None)

    args = parser.parse_args()
    print(ga_solve(args.filename, args.nogui, args.maxtime))
