import pygame
import math
import random
import sys
import time
from pygame.locals import KEYDOWN, QUIT, MOUSEBUTTONDOWN, K_RETURN

cities = []
screen = None
city_color = (10,10,200) # blue
summary_color = (255, 255, 255)
city_font_size = 16 # pixels
summary_font_size = 26
screen_size = (500, 500)
city_radius = 2
city_font = None
summary_font = None

def citiesFromFile(file):
    f = open(file, 'r')
    cities = []
    for line in f:
        comp = line.rstrip('\n').split(' ')
        city = (comp[0], (int(comp[1]), int(comp[2])))
        cities.append(city)

    return cities

def drawCities(positions, connected = False, generation = -1, distance = -1):
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
            text = city_font.render('Generation n°' + str(generation) + '; Distance = ' + str(round(distance, 2)), True, summary_color, (0, 0, 0))
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
    
    if gui:
        setupGui()
    
    if file != None:
        cities = citiesFromFile(file)
    else:
        citiesByMouse()
    drawCities(cities)
    print(cities)
    initial_population(cities)
    print(cities)
    t1 = time.time()
    gen = 0
    while maxtime == 0 or time.time() - t1 <= maxtime:
        print(total_distance(cities))
        initial_population(cities)
        drawCities(cities, True, gen, total_distance(cities))
        gen += 1

def total_distance(cities):
    distance = 0
    c2 = None
    for c in cities:
        c1 = c2
        c2 = c
        if c1 != None and c2 != None:
            distance += distance_between(c1, c2)

    distance += distance_between(cities[0], cities[len(cities) -1])
    return distance

def distance_between(city1, city2):
    return math.sqrt(pow(city1[1][0] - city2[1][0], 2) + pow(city1[1][1] - city2[1][1], 2))

def initial_population(cities):
    random.shuffle(cities)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Voyageur de commerce')
    parser.add_argument('--nogui', default=True, action='store_false')
    parser.add_argument('--maxtime', type=int, default=0)
    parser.add_argument('filename', nargs='?', default=None)

    args = parser.parse_args()
    ga_solve(args.filename, args.nogui, args.maxtime)