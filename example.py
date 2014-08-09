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
print board.weights.total

# show button state(boolean)
print board.button

# toggle led of front button
board.toggle_led()
