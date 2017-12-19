# Copyright 2017 D.G. MacCarthy <http://dmaccarthy.github.io>
#
# This file is part of "sc8pr".
#
# "sc8pr" is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# "sc8pr" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "sc8pr".  If not, see <http://www.gnu.org/licenses/>.

"""
This program recreates the "chimp" program from the pygame examples and
tutorial (https://www.pygame.org/docs/tut/ChimpLineByLine.html), but using
sc8pr rather than using pygame directly (except for sound). This version
loads image and sound files directly from the [pygame]/examples/data folder.
"""

from random import randint
import os.path, pygame
from sc8pr import Sketch, Image, BOTH, TOP, TOPLEFT, TOPRIGHT
from sc8pr.sprite import Sprite
from sc8pr.text import Text, Font, BOLD
from sc8pr.misc.effect import ReplaceColor

def loadImage(filename):
    "Load image file and change background to transparent"
    img = Image(filename)
    color = img.original.get_at((0,0))
    return ReplaceColor(color).apply(img)

def setup(sk):
    "Add all content to the sketch"

    # Add text to the sketch
    font = {"font":Font.mono(), "fontStyle":BOLD}
    sk += Text(0).config(name="Score", anchor=TOPLEFT, color="red", **font)
    text = "Pummel the Chimp, and Win $$$"
    sk += Text(text).config(pos=(sk.width-1,0), anchor=TOPRIGHT, **font)

    # Add fist
    folder = os.path.split(pygame.__file__)[0] + "/examples/data/"
    img = loadImage(folder + "fist.bmp")
    sk += Image(img).config(pos=sk.center, anchor=TOP).bind(ondraw)

    # Add chimp sprite
    img = loadImage(folder + "chimp.bmp")
    sk += Sprite(img).config(name="Chimp", pos=(48,48),
        vel=(10,0), bounce=BOTH).bind(ondraw=chimpDraw)

    # Load audio files
    audio = "punch.wav", "whiff.wav"
    sk.sounds = [pygame.mixer.Sound(folder + f) for f in audio]

    # Bind click event handler; hide cursor
    sk.bind(onclick)
    sk.cursor = False

def onclick(sk, ev):
    "Event handler for mouse clicks"
    chimp = sk["Chimp"]
    if chimp.contains(sk.mouse.pos):
        chimp.oldVel = chimp.vel
        chimp.config(spin=-8, vel=(0,0))
        sk["Score"].add(1)
        sound = 0
    else: sound = 1
    sk.sounds[sound].play()

def chimpDraw(chimp):
    "Stop spinning after a random amount of time"
    Sprite.ondraw(chimp)   # Call default handler!!
    if chimp.spin and randint(1, 30) == 1:
        chimp.spin = chimp.angle = 0
        chimp.vel = chimp.oldVel

def ondraw(fist):
    "Make fist follow the mouse"
    fist.pos = fist.sketch.mouse.pos

# Run the sketch
Sketch((468,60)).play("Monkey Fever")
