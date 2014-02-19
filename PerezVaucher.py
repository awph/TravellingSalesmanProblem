import pygame
import math
import random
import sys
import time
from pygame.locals import KEYDOWN, QUIT, MOUSEBUTTONDOWN, K_RETURN

# GUI
screen = None
city_color = (10, 10, 200) # blue
summary_color = (255, 255, 255)
city_font_size = 16 # pixels
summary_font_size = 26
screen_size = (500, 500)
city_radius = 2
city_font = None
summary_font = None

cities = []
elitism_percent = 30 / 100
population_size = 100


def citiesFromFile(file):
    f = open(file, 'r')
    cities = []
    for line in f:
        comp = line.rstrip('\n').split(' ')
        city = (comp[0], (int(comp[1]), int(comp[2])))
        cities.append(city)

    return cities


def drawCities(positions, connected=False, generation=-1, distance=-1):
    if screen == None:
        print(positions)
    else:
        screen.fill(0)
        for pos in positions:
            text = city_font.render(pos[0], True, city_color, (0, 0, 0))
            textrect = text.get_rect()
            textrect.centerx = pos[1][0]
            textrect.centery = pos[1][1]
            screen.blit(text, textrect)

        if connected:
            pygame.draw.lines(screen, city_color, True, [x[1] for x in cities])

        if generation != -1 and distance != -1:
            text = city_font.render('Generation n°' + str(generation) + '; Distance = ' + str(round(distance, 2)), True,
                                    summary_color, (0, 0, 0))
            textrect = text.get_rect()
            textrect.centerx = screen_size[0] / 2.0
            textrect.centery = screen_size[1] - summary_font_size / 4.0
            screen.blit(text, textrect)

        pygame.display.flip()


def setupGui():
    global screen, city_font, summary_font
    pygame.init()
    city_font = pygame.font.SysFont(None, city_font_size)
    summary_font = pygame.font.SysFont(None, summary_font_size)
    pygame.display.set_mode(screen_size)
    pygame.display.set_caption('TSP')
    screen = pygame.display.get_surface()


def citiesByMouse():
    global screen
    wasGui = True
    if screen == None:
        wasGui = False
        setupGui()

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
                drawCities(cities)

    if not wasGui:
        pygame.quit()
        screen = None


def ga_solve(file=None, gui=True, maxtime=0):
    global cities
    t1 = time.time()

    if gui:
        setupGui()

    if file is not None:
        cities = citiesFromFile(file)
    else:
        citiesByMouse()
    drawCities(cities)

    # Initial population
    population = initial_population(cities, population_size)

    gen = 0
    fittest = None

    while maxtime == 0 or time.time() - t1 <= maxtime:
        # Evaluate
        evaluate(population)
        # Check the fittest
        if fittest is None or fittest[1] > population[0][1]:
            fittest = population[0].copy()
            drawCities(fittest[0], True, gen, fittest[1])
        # Sort for selection
        population.sort(key=lambda s: s[1])
        # Selection
        elites = []
        for i in range(0, int(len(population) * elitism_percent)):
            elites.append(population[i])
        # Crossover
        childs = cross(elites)
        for i in range(len(population) - len(childs), len(population)):
            population[i] = childs[len(population) - i - len(childs)]
        # Mutate
        mutate(population[random.randint(0, len(population) - 1)][0])
        gen += 1


def evaluate(population):
    for solution in population:
        solution[1] = total_distance(solution[0])


def cross(subpopulation):
    crossed = []
    s2 = None
    for solution in subpopulation:
        s1 = s2
        s2 = solution[0]
        p1 = random.randint(1, len(s2) - 2)
        p2 = p1
        while p1 == p2:
            p2 = random.randint(1, len(s2) - 2)
        if p1 > p2:
            temp = p2
            p2 = p1
            p1 = temp
        if s1 is not None and s2 is not None:
            childs = cross_two_solutions(s1, s2, p1, p2)
            crossed += childs

    return crossed


def cross_two_solutions(solution1, solution2, p1, p2):
    middle_cities1 = []
    middle_cities2 = []
    for i in range(p1, p2):
        middle_cities1.append(solution1[i])
    for i in range(p1, p2):
        middle_cities2.append(solution2[i])
    pack_cities(solution1, middle_cities2, p1, p2)
    pack_cities(solution2, middle_cities1, p1, p2)

    for i in range(p1, p2):
        solution1[i] = middle_cities2[i - p1]
        solution2[i] = middle_cities1[i - p1]

    solution1 = [solution1, None]
    solution2 = [solution2, None]

    if is_solutions_equal(solution1, solution2):
        return [solution1]
    return [solution1, solution2]


def mutate(solution):
    p1 = random.randint(0, len(solution) - 1)
    p2 = p1
    while p1 == p2:
        p2 = random.randint(0, len(solution) - 1)
    temp = solution[p1]
    solution[p1] = solution[p2]
    solution[p2] = temp


def is_solutions_equal(solution1, solution2):
    for i in range(0, len(solution1)):
        if solution1[0][i][0] != solution2[0][i][0]:
            return False
    return True


def pack_cities(solution, middle_cities, p1, p2):
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


def total_distance(cities):
    distance = 0
    c2 = None
    for c in cities:
        c1 = c2
        c2 = c
        if c1 is not None and c2 is not None:
            distance += distance_between(c1, c2)

    distance += distance_between(cities[0], cities[len(cities) - 1])
    return distance


def distance_between(city1, city2):
    return math.sqrt(pow(city1[1][0] - city2[1][0], 2) + pow(city1[1][1] - city2[1][1], 2))


def initial_population(cities, quantity):
    population = []
    while len(population) < quantity:
        solution = cities.copy()
        random.shuffle(solution)
        population.append([solution, None])
    return population


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Voyageur de commerce')
    parser.add_argument('--nogui', default=True, action='store_false')
    parser.add_argument('--maxtime', type=int, default=0)
    parser.add_argument('filename', nargs='?', default=None)

    args = parser.parse_args()
    ga_solve(args.filename, args.nogui, args.maxtime)