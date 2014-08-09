# -*- coding: utf-8 -*-

import wiiboard

board = wiiboard.Board()

# tuple of weights of each corner
# (AA, BB, CC, DD)
# +----------------+
# |  BB       AA   |
# |  DD       CC   |
# |     Button     |
# +----------------+


# show weight of each corner
print board.weights.topright
print board.weights.topleft
print board.weights.bottomright
print board.weights.bottomleft

# show total weight
print board.weights.total

# show whether button pressed(boolean)
print board.button

# toggle led of front button
board.toggle_led()
