Wiiboard
=================
Simple Library to interface with Nintendo Balance Wiiboard


Requirements
================
- Nintendo Wiiboard RVL-WBC-01
- Pybluez(https://code.google.com/p/pybluez/) module


Example
===================
```python

import wiiboard

board = wiiboard.Board()


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
```
