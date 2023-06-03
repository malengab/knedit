# How to run:
'''
  pypy s2bu.py  #or
  python3 s2bu.py 

Requires pygame:
  python3 -m pip install pygame
'''
import math
import os
# Suppress "Hello from pygame" text in console
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'
import pygame
pg = pygame
import pickle
from random import random
from pygame.locals import *
from PIL import Image, ImageDraw

# Window coords
#  x is left to right
#  y is top to bottom

# World coords
#   Unit squares (between integer points)
#   x is left to right
#   y is top to bottom


white = (255, 255, 255)
black = (0, 0, 0)
red = (255, 0, 0)
blue = (0, 255, 0)
green = (0, 0, 255)
purple = (255, 255, 0)
COLORS = [white, red]
num_colors = len(COLORS)

resolution = (1000, 1000)
pygame.init()
screen = pygame.display.set_mode(resolution, pygame.RESIZABLE)
# screen.set_caption("Example resizable window")
# JayBird X4 = J'vla Bird X4 : blä X4
# X3 = OK.


def nbhs(i, j):
  for ii in range(-1, 2):
    for jj in range(-1, 2):
      if not (ii == 0 and jj == 0):
        yield (i + ii, j + jj)


def nbhs_set(active):
  to_scan = set(active)
  for (i, j) in active:
    for (ii, jj) in nbhs(i, j):
      to_scan.add((ii, jj))
  return to_scan


def gol(color):
  result = dict()
  active = [k for k in color if color[k] == 1]
  to_scan = nbhs_set(active)
  for c in to_scan:
    ct = 0
    for q in nbhs(*c):
      if q in active:
        ct += 1
    if c in active:
      if (ct == 2 or ct == 3):
        result[c] = 1
    else:
      if ct == 3:
        result[c] = 1
  return result


# Draws the slice between (x1,y1) and (x2,y2) in game coords to
# the full screen.
# The real world is made of unit squares which have their own colors.
class Game():
  def __init__(self):
    pygame.init()
    pygame.mixer.quit()
    self.screen = pygame.display.set_mode(resolution)
    self.clock = pygame.time.Clock()
    self.running = True
    self.color = dict()
    self.history = list()
    self.selection1 = None  # region selected with the mouse
    self.selection2 = None
    self.holdable = set(
        [pg.K_LCTRL, pg.K_h, pg.K_g, pg.K_UP, pg.K_DOWN, pg.K_LEFT, pg.K_RIGHT])
    self.holding = set()  # keys that are being held down
    # This describes what part of the real world coordinates
    # we are looking at (mapped to the full screen)
    self.x1 = 0.0
    self.x2 = 50.0
    self.y1 = 0.0
    self.y2 = 50.0

  # map x1 to 0, x2 to resolution[0]
  # map y1 to 0, y2 to resolution[1].

  def to_screen(self, x, y):
    return (int((x - self.x1) / (self.x2 - self.x1) * float(resolution[0])),
            int((y - self.y1) / (self.y2 - self.y1) * float(resolution[1])))

  # map 0 to x1, resolution[0] to x2
  # map 0 to y1, resolution[1] to y2
  def from_screen(self, x, y):
    return (self.x1 + (self.x2 - self.x1) * x / float(resolution[0]),
            self.y1 + (self.y2 - self.y1) * y / float(resolution[1]))

  def color_of_square(self, k, l):
    if (k, l) in self.color:
      return COLORS[self.color[k, l]]
    else:
      return COLORS[0]

  def get_draw_steps_unit(self, k, l):
    lines = []
    rects = []
    (sx, sy) = self.to_screen(k, l)
    (sxp, syp) = self.to_screen(k + 1, l + 1)
    color = self.color_of_square(k, l)
    if self.selection1 and self.selection2:
      k1, l1 = self.selection1
      k2, l2 = self.selection2
      if k1 <= k <= k2 and l1 <= l <= l2:
        r, g, b = color
        r //= 2
        g //= 2
        b //= 2
        color = (r, g, b)
    rects.append((color, (sx+1, sy+1, sxp - sx-1, syp - sy-1)))
    lines.append((black, ((sx, sy), (sx, syp))))
    lines.append((black, ((sx, sy), (sxp, sy))))
    return rects, lines

  def draw_unit(self, k, l):
    rects, lines = self.get_draw_steps_unit(k, l)
    for l in lines:
      pygame.draw.line(self.screen, l[0], *l[1])
    for r in rects:
      pygame.draw.rect(self.screen, r[0], pygame.Rect(r[1]))


  def get_all_draw_steps(self):
    rects = []
    lines = []
    for k in range(int(self.x1), int(self.x2)):
      for l in range(int(self.y1), int(self.y2)):
        r, l = self.get_draw_steps_unit(k, l)
        rects += r
        lines += l
    return rects, lines

  def draw_all(self):
    rects, lines = self.get_all_draw_steps()
    for r in rects:
      pygame.draw.rect(self.screen, r[0], pygame.Rect(r[1]))
    for l in lines:
      pygame.draw.line(self.screen, l[0], *l[1])

  def draw_all_to_obj(self, draw_obj):
    rects, lines = self.get_all_draw_steps()
    for r in rects:
      x, y, w, h = r[1]
      draw_obj.rectangle((x, y, x + w, y + h), fill=r[0])
    for l in lines:
      draw_obj.line(l[1], fill=l[0])

  def handleEvents(self):
    for event in pygame.event.get():
      if event.type == QUIT:
        self.running = False
      elif event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
          self.running = False
        elif event.key == pygame.K_s:
          pickle.dump(self.color, open("img.p", "wb"))
        elif event.key == pygame.K_l:
          self.color = pickle.load(open("img.p", "rb"))
          self.history = []
          self.draw_all()
        elif event.key == pg.K_DELETE:
          if self.selection1 and self.selection2:
            (k1, l1) = self.selection1
            (k2, l2) = self.selection2
            to_rm = set()
            for (k, l) in self.color:
              if k1 <= k <= k2 and l1 <= l <= l2:
                to_rm.add((k, l))
            for (k, l) in to_rm:
              del self.color[k, l]
          self.draw_all()
        elif event.key == pygame.K_s:
          pickle.dump(self.color, open("img.p", "wb"))
        elif event.key == pygame.K_l:
          self.color = pickle.load(open("img.p", "rb"))
          self.history = []
          self.draw_all()
        elif event.key == pygame.K_p:  # PDF
          image = Image.new("RGB", resolution, "white")
          draw = ImageDraw.Draw(image)
          self.draw_all_to_obj(draw)
          image.save("img.pdf")
        elif event.key in self.holdable:
          self.holding.add(event.key)
      elif event.type == pygame.KEYUP:
        if event.key == pygame.K_ESCAPE:
          self.running = False
        elif event.key in self.holdable:
          self.holding.remove(event.key)
      elif event.type == pygame.MOUSEBUTTONDOWN:
        x, y = self.from_screen(*event.pos)
        k, l = round(x - 0.5), round(y - 0.5)
        if event.button == 3:  # RIGHTBUTTON
          if not (k, l) in self.color:
            self.color[k, l] = 0
          self.color[k, l] = (self.color[k, l] + 1) % num_colors
          self.draw_unit(k, l)
        elif event.button == 1:  # LEFTBUTTON
          self.holding.add("ml")
          if self.selection1:
            self.selection1 = None
          else:
            self.selection1 = (k, l)
        elif event.button == 2:  # MIDDLEBUTTON : attempt to paste selection.
          if self.selection1 and self.selection2:
            self.history.append(self.color)
            (k1, l1) = self.selection1
            (k2, l2) = self.selection2
            to_add = set()
            for (kp, lp) in self.color:
              if k1 <= kp <= k2 and l1 <= lp <= l2:
                if self.color[kp, lp] == 1:
                  to_add.add((kp - k1 + k, lp - l1 + l))
            ng = dict()
            for (k, l) in self.color:
              if not pg.K_LCTRL in self.holding or not (k1 <= k <= k2 and l1 <= l <= l2):
                ng[k, l] = self.color[k, l]
            for x in to_add:
              ng[x] = 1
            self.color = ng
            self.draw_all()

      elif event.type == pygame.MOUSEBUTTONUP:
        x, y = self.from_screen(*event.pos)
        if event.button == 1:
          self.holding.remove("ml")
        elif event.button == 4:  # scroll up
          zoom_factor = 1.1
          (tx, ty) = self.from_screen(*event.pos)
          self.x1 = tx - zoom_factor * (tx - self.x1)
          self.y1 = ty - zoom_factor * (ty - self.y1)
          self.x2 = tx + zoom_factor * (self.x2 - tx)
          self.y2 = ty + zoom_factor * (self.y2 - ty)
          self.draw_all()
        elif event.button == 5:  # scroll down
          if self.x2 - self.x1 > 2 and self.y2 - self.y1 > 2:  # not quite the right condition
            zoom_factor = 0.75
            (tx, ty) = self.from_screen(*event.pos)
            self.x1 = tx - zoom_factor * (tx - self.x1)
            self.y1 = ty - zoom_factor * (ty - self.y1)
            self.x2 = tx + zoom_factor * (self.x2 - tx)
            self.y2 = ty + zoom_factor * (self.y2 - ty)
            self.draw_all()
#      elif event.type == pygame.MOUSEMOTION:
      elif event.type == pygame.VIDEORESIZE:
        print(event)
        # surface = pygame.display.set_mode((event.w, event.h),pygame.RESIZABLE)

  def run(self):
    self.draw_all()
    while self.running:
      self.handleEvents()
      if pg.K_UP in self.holding:
        inc = 0.01 * (self.y2 - self.y1)
        self.y1 -= inc
        self.y2 -= inc
        self.draw_all()
      if pg.K_DOWN in self.holding:
        inc = 0.01 * (self.y2 - self.y1)
        self.y1 += inc
        self.y2 += inc
        self.draw_all()
      if pg.K_LEFT in self.holding:
        inc = 0.01 * (self.x2 - self.x1)
        self.x1 -= inc
        self.x2 -= inc
        self.draw_all()
      if pg.K_RIGHT in self.holding:
        inc = 0.01 * (self.x2 - self.x1)
        self.x1 += inc
        self.x2 += inc
        self.draw_all()
      if pg.K_g in self.holding:
        self.history.append(self.color)
        self.color = gol(self.color)
        self.draw_all()
      if pg.K_h in self.holding:
        if len(self.history) > 0:
          self.color = self.history.pop()
          self.draw_all()
      if "ml" in self.holding:
        x, y = self.from_screen(*pygame.mouse.get_pos())
        k, l = round(x - 0.5), round(y - 0.5)
        change = True
        if self.selection2:
          u, v = self.selection2
          change = (u != k or v != l)
        self.selection2 = k, l
        if change:
          self.draw_all()
      self.clock.tick(60)
      pygame.display.flip()


docstring = """
LMB -- left mouse button
MMB -- middle mouse button

EDIT

Make a selection by marking two corners with LMB.
When a selection is active (faded out), you can:
  press MMB:
    copy/paste to cursor
  press left ctrl and MMB:
    cut from selection to cursor
  press Delete
    paint selection white
  
SCROLL

up/left/down/right
mouse scroll wheel

HISTORY

press h:
  undo last action (among undo-eligible actions)
press s:
  save editor content to file `img.p`
press l:
  load editor content from file `img.p`
press p:
  print editor view as image to file `img.pdf`

"""
print(docstring)

game = Game()
game.run()
