import os
import time
from platform import system
from ctypes import windll
from random import random
from datetime import datetime
import json
import pprint


SAMPLES = {
    'glider': {
        'world': [
            [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        ],
        'max_step': 40,
    },
    'galaxy': {
        'world': [
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 0, 0],
            [0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0],
            [0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0],
            [0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0],
            [0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0],
            [0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0],
            [0, 0, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        ],
        'max_step': 45,
    },
}


class GameOfLife:
    def __init__(self, title='game_of_life', x=30, y=15, world=None,
                 max_step=100, wait_time=0.05, life='■', ratio=0.5,
                 loop=False, torus=False, json_file=''):
        self.title = title
        self.x = x
        self.y = y
        rand = False
        if title in SAMPLES:
            if 'world' in SAMPLES[title]:
                world = SAMPLES[title]['world']
            if 'max_step' in SAMPLES[title]:
                max_step = SAMPLES[title]['max_step']
        if world is not None:
            self.x = len(world[0])
            self.y = len(world)
            self.world = [[x for x in row] for row in world]
        else:
            rand = True
            self.world = [[1 if random() < ratio else 0 for _ in range(x)]
                          for _ in range(y)]
        self.max_step = max_step
        self.wait_time = wait_time
        self.life = life
        self.ratio = ratio
        self.loop = loop
        self.torus = torus

        if json_file is not None:
            rand = False
            self.load(json_file)

        self.dirs = [
            (-1, -1), (0, -1), (1, -1),
            (-1,  0),          (1,  0),
            (-1,  1), (0,  1), (1,  1),
        ]
        self.step = 1
        self.console = Console(self.x, self.y, self.title, self.life)

        if rand:
            self.dump()

    def load(self, json_file):
        try:
            with open(json_file, 'r') as f:
                settings = json.load(f)
                self.title = settings['title']
                self.x = settings['x']
                self.y = settings['y']
                self.world = settings['world']
                self.max_step = settings['step']
                self.wait_time = settings['wait']
                self.life = settings['life']
                self.ratio = settings['ratio']
                self.loop = settings['loop']
                self.torus = settings['torus']
        except FileNotFoundError:
            pass

    def start(self):
        try:
            self.console.setup()
            while True:
                self.console.display(self.world, self.step)
                if not self.loop and self.step == self.max_step:
                    break
                self.update()
                self.wait()
        except KeyboardInterrupt:
            return
        finally:
            self.console.teardown()

    def update(self):
        new_world = [[self.new_cell(x, y) for x in range(self.x)]
                     for y in range(self.y)]
        self.world = [[x for x in row] for row in new_world]
        self.step += 1

    def new_cell(self, x, y):
        alive = self.count_alive(x, y)
        if self.world[y][x]:
            return 1 if alive == 2 or alive == 3 else 0
        return 1 if alive == 3 else 0

    def count_alive(self, x, y):
        alive = 0
        for dx, dy in self.dirs:
            next_x, next_y = x + dx, y + dy
            if self.torus:
                next_x %= self.x
                next_y %= self.y
            if (0 <= next_x < self.x) and (0 <= next_y < self.y):
                if self.world[next_y][next_x]:
                    alive += 1
        return alive

    def wait(self):
        time.sleep(self.wait_time)

    def dump(self):
        now = datetime.now().strftime('%Y%m%d%H%M%S')
        json_file = 'world' + now + '.json'
        settings = {
            'title': self.console.title,
            'x': self.x,
            'y': self.y,
            'world': self.world,
            'step': self.max_step,
            'wait': self.wait_time,
            'life': self.console.life,
            'ratio': self.ratio,
            'loop': self.loop,
            'torus': self.torus,
        }
        with open(json_file, 'w') as f:
            output = pprint.pformat(settings, indent=4,
                                    width=1000, sort_dicts=False)
            output = output.replace("'", '"')
            output = output.replace('True', 'true')
            output = output.replace('False', 'false')
            f.write(output)


class Console:
    def __init__(self, x, y, title, life):
        self.x = x
        self.y = y
        self.title = title
        self.life = life
        if 'win' in system().lower():
            self.enable_win_escape_sequence()

    def enable_win_escape_sequence(self):
        kernel = windll.kernel32
        kernel.SetConsoleMode(kernel.GetStdHandle(-11), 7)

    def setup(self):
        self.cls()
        self.cursor_hyde()

    def teardown(self):
        self.cursor_show()

    def cls(self):
        os.system('cls')

    def cursor_hyde(self):
        print('\033[?25l', end='')

    def cursor_show(self):
        print('\033[?25h', end='')

    def cursor_up(self, n):
        print(f'\033[{n}A', end='')

    def display(self, world, step):
        if step > 1:
            self.cursor_up(self.y + 4)
        self.display_title()
        self.display_world(world)
        self.display_step(step)

    def display_title(self):
        print(f'{self.title} ({self.x} x {self.y})')

    def display_world(self, world):
        print('┌' + '─' * (self.x * 2) + '┐')
        line = []
        for y in range(self.y):
            cells = ''.join([self.life if i else '  ' for i in world[y]])
            line.append('│' + cells + '│')
        print('\n'.join(line))
        print('└' + '─' * (self.x * 2) + '┘')

    def display_step(self, step):
        print(f'step = {step}')


if __name__ == '__main__':
    import sys
    argv = sys.argv
    if len(argv) == 2 and argv[1] in SAMPLES:
        GameOfLife(title=argv[1]).start()
    elif len(argv) == 3 and int(argv[1]) > 0 and int(argv[2]) > 0:
        GameOfLife(x=int(argv[1]), y=int(argv[2])).start()
    else:
        GameOfLife().start()
